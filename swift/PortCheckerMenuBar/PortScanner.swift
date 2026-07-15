import AppKit
import Combine
import Foundation
import SwiftUI
import UserNotifications

// MARK: - Models

struct PortService: Codable, Identifiable, Hashable {
    let pid: Int
    let port: Int
    let app: String
    let project: String
    let user: String
    let command: String
    let address: String
    let isSystem: Bool
    let isExposed: Bool
    let exposureReason: String?
    let fingerprint: ServiceFingerprint?
    let securityIssues: [SecurityIssue]
    
    var id: String { "\(pid):\(port)" }
    
    enum CodingKeys: String, CodingKey {
        case pid
        case port
        case app
        case project
        case user
        case command
        case address
        case isSystem = "is_system"
        case isExposed = "is_exposed"
        case exposureReason = "exposure_reason"
        case fingerprint
        case securityIssues = "security_issues"
    }
}

struct ServiceFingerprint: Codable, Hashable {
    let service: String
    let version: String
    let transportProtocol: String

    enum CodingKeys: String, CodingKey {
        case service, version
        case transportProtocol = "protocol"
    }
}

struct SecurityIssue: Codable, Hashable {
    let severity: String
    let message: String
    let recommendation: String
}

struct Favorite: Codable, Identifiable, Hashable {
    let port: Int
    let name: String
    let note: String
    
    var id: Int { port }
}

struct ServiceGroup: Identifiable {
    let name: String
    let services: [PortService]
    var id: String { name }
}

// MARK: - Port Scanner

@MainActor
final class PortScanner: ObservableObject {
    @Published var services: [PortService] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var showSystemServices: Bool {
        didSet {
            UserDefaults.standard.set(showSystemServices, forKey: showSystemKey)
            refresh()
        }
    }
    @Published private(set) var cliPath: String {
        didSet {
            UserDefaults.standard.set(cliPath, forKey: cliPathKey)
        }
    }
    @Published var favorites: [Favorite] = []
    
    private let cliPathKey = "portchecker_cliPath"
    private let showSystemKey = "portchecker_showSystem"
    private var refreshTimer: Timer?
    private var previousServices: [PortService] = []
    
    let appVersion = "1.0.0"
    
    var bundledCliPath: String? {
        Bundle.main.path(forResource: "portchecker", ofType: nil)
    }

    nonisolated private static var bundledCLIPath: String? {
        Bundle.main.path(forResource: "portchecker", ofType: nil)
    }
    
    init() {
        let defaults = UserDefaults.standard
        self.cliPath = defaults.string(forKey: cliPathKey) ?? ""
        self.showSystemServices = defaults.bool(forKey: showSystemKey)

        loadFavorites()
        setupAutoRefresh()
        requestNotificationPermission()
    }
    
    // MARK: - Computed Properties
    
    var hasSecurityIssues: Bool {
        services.contains { !$0.securityIssues.isEmpty && !$0.isSystem }
    }
    
    var groupedServices: [String: [PortService]] {
        var groups: [String: [PortService]] = [:]
        let favoritePorts = Set(favorites.map(\.port))
        
        var favoritesList: [PortService] = []
        var systemList: [PortService] = []
        var projects: [String: [PortService]] = [:]
        
        for service in services {
            if favoritePorts.contains(service.port) {
                favoritesList.append(service)
            } else if service.isSystem {
                systemList.append(service)
            } else {
                let project = service.project
                projects[project, default: []].append(service)
            }
        }
        
        if !favoritesList.isEmpty {
            groups["__favorites"] = favoritesList.sorted { $0.port < $1.port }
        }
        
        for (project, services) in projects {
            groups[project] = services.sorted { $0.port < $1.port }
        }
        
        if !systemList.isEmpty {
            groups["__system"] = systemList.sorted { $0.port < $1.port }
        }
        
        return groups
    }

    var sidebarGroups: [ServiceGroup] {
        let groups = groupedServices
        var result: [ServiceGroup] = []
        if let favorites = groups["__favorites"] { result.append(ServiceGroup(name: "Favorites", services: favorites)) }
        for project in groups.keys.filter({ $0 != "__favorites" && $0 != "__system" }).sorted() {
            result.append(ServiceGroup(name: project == "Unknown" ? "Other" : project, services: groups[project] ?? []))
        }
        if let system = groups["__system"] { result.append(ServiceGroup(name: "System Services", services: system)) }
        return result
    }
    
    // MARK: - Refresh
    
    func refresh() {
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = nil
        let showSystem = showSystemServices
        let configuredCLIPath = cliPath
        
        DispatchQueue.global(qos: .userInitiated).async {
            let result = Self.fetchServices(showSystem: showSystem, configuredCLIPath: configuredCLIPath)
            
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.isLoading = false
                
                switch result {
                case .success(let services):
                    let previous = self.previousServices
                    self.services = services
                    self.previousServices = services
                    self.checkForChanges(previous: previous, current: services)
                case .failure(let error):
                    self.services = []
                    self.errorMessage = error.message
                }
            }
        }
    }
    
    private func setupAutoRefresh() {
        refreshTimer?.invalidate()
        guard UserDefaults.standard.bool(forKey: "autoRefresh") else { return }
        let interval = max(10, UserDefaults.standard.double(forKey: "autoRefreshInterval"))
        refreshTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self, !self.isLoading else { return }
                self.refresh()
            }
        }
    }

    func configureAutoRefresh() {
        setupAutoRefresh()
    }
    
    private func checkForChanges(previous: [PortService], current: [PortService]) {
        guard UserDefaults.standard.bool(forKey: "showNotifications") else { return }
        
        let previousPorts = Set(previous.map(\.port))
        let currentPorts = Set(current.map(\.port))
        
        let started = current.filter { !previousPorts.contains($0.port) }
        let stopped = previous.filter { !currentPorts.contains($0.port) }
        
        for service in started {
            showNotification(
                title: "Service Started",
                body: "\(service.app) on port \(service.port)"
            )
        }
        
        for service in stopped {
            showNotification(
                title: "Service Stopped",
                body: "\(service.app) on port \(service.port)"
            )
        }
    }
    
    private func showNotification(title: String, body: String) {
        let notification = UNMutableNotificationContent()
        notification.title = title
        notification.body = body
        notification.sound = .default
        
        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: notification,
            trigger: nil
        )
        
        UNUserNotificationCenter.current().add(request)
    }
    
    // MARK: - CLI Path
    
    @MainActor func chooseCliPath() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.message = "Select the portchecker CLI executable"
        panel.prompt = "Select"
        
        if panel.runModal() == .OK, let url = panel.url {
            cliPath = url.path
            refresh()
        }
    }
    
    private func resolveCliPath() -> String? {
        Self.resolveCliPath(configuredPath: cliPath)
    }

    nonisolated private static func resolveCliPath(configuredPath: String) -> String? {
        // Check configured path
        if isExecutable(path: configuredPath) {
            return configuredPath
        }
        
        // Check bundled CLI
        if let bundled = bundledCLIPath, isExecutable(path: bundled) {
            return bundled
        }
        
        // Check PATH
        if let found = findInPath("portchecker") {
            return found
        }
        
        return nil
    }
    
    nonisolated private static func isExecutable(path: String) -> Bool {
        guard !path.isEmpty else { return false }
        return FileManager.default.isExecutableFile(atPath: path)
    }
    
    nonisolated private static func findInPath(_ name: String) -> String? {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/which")
        process.arguments = [name]
        let outputPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = Pipe()
        
        do {
            try process.run()
        } catch {
            return nil
        }
        
        process.waitUntilExit()
        guard process.terminationStatus == 0 else { return nil }
        
        let data = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let path = String(data: data, encoding: .utf8)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        
        return path?.isEmpty == false ? path : nil
    }
    
    // MARK: - Service Fetching
    
    nonisolated private static func fetchServices(showSystem: Bool, configuredCLIPath: String) -> Result<[PortService], CLIError> {
        guard let cli = resolveCliPath(configuredPath: configuredCLIPath) else {
            return .failure(CLIError(message: "CLI not found. Please install portchecker CLI or set path in Settings."))
        }
        
        var args = ["scan", "--json", "--external"]
        if showSystem {
            args.append("--show-system")
        }
        
        do {
            let output = try runCLI(cliPath: cli, args: args)
            let trimmed = output.trimmingCharacters(in: .whitespacesAndNewlines)
            
            guard !trimmed.isEmpty else {
                return .success([])
            }
            
            guard let data = trimmed.data(using: .utf8) else {
                return .failure(CLIError(message: "Failed to decode CLI output"))
            }
            
            let decoded = try JSONDecoder().decode([PortService].self, from: data)
            return .success(decoded)
            
        } catch let error as CLIError {
            return .failure(error)
        } catch {
            return .failure(CLIError(message: error.localizedDescription))
        }
    }
    
    nonisolated private static func runCLI(cliPath: String, args: [String]) throws -> String {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: cliPath)
        process.arguments = args
        
        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe
        
        do {
            try process.run()
        } catch {
            throw CLIError(message: "Failed to run CLI at \(cliPath)")
        }
        
        process.waitUntilExit()
        
        let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
        let output = String(data: outputData, encoding: .utf8) ?? ""
        
        guard process.terminationStatus == 0 else {
            let errorText = String(data: errorData, encoding: .utf8) ?? ""
            throw CLIError(message: errorText.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        
        return output
    }
    
    // MARK: - Process Control
    
    func kill(service: PortService) {
        guard !service.isSystem else { return }
        
        runStop(services: [service])
    }
    
    func killAll() {
        let targets = services.filter { !$0.isSystem }
        guard !targets.isEmpty else { return }
        
        runStop(services: targets)
    }
    
    private func runStop(services: [PortService]) {
        isLoading = true
        errorMessage = nil
        
        guard let cli = resolveCliPath() else {
            errorMessage = "CLI not found"
            isLoading = false
            return
        }

        DispatchQueue.global(qos: .userInitiated).async {
            defer {
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    self.isLoading = false
                    self.refresh()
                }
            }
            
            for service in services {
                _ = try? Self.runCLI(cliPath: cli, args: [
                    "stop",
                    "--pid", "\(service.pid)",
                    "--yes"
                ])
            }
        }
    }
    
    // MARK: - Favorites
    
    func loadFavorites() {
        guard let cli = resolveCliPath(), let output = try? Self.runCLI(cliPath: cli, args: ["fav-list", "--json"]),
              let data = output.data(using: .utf8), let decoded = try? JSONDecoder().decode([Favorite].self, from: data) else {
            favorites = []
            return
        }
        favorites = decoded
    }
    
    func saveFavorites() {
        // CLI owns the shared favorites file. Mutations happen through its commands.
    }
    
    func addFavorite(port: Int, name: String, note: String) {
        guard !favorites.contains(where: { $0.port == port }) else { return }
        guard let cli = resolveCliPath() else { return }
        _ = try? Self.runCLI(cliPath: cli, args: ["fav-add", "\(port)", name, "--note", note])
        loadFavorites()
        refresh()
    }
    
    func removeFavorite(_ favorite: Favorite) {
        guard let cli = resolveCliPath() else { return }
        _ = try? Self.runCLI(cliPath: cli, args: ["fav-remove", "\(favorite.port)"])
        loadFavorites()
        refresh()
    }
    
    private struct CLIError: LocalizedError {
        let message: String
        var errorDescription: String? { message }
    }
}

// MARK: - Notification Setup

extension PortScanner {
    func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
    }
}
