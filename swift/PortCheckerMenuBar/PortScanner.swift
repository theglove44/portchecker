import AppKit
import Combine
import Foundation
import SwiftUI

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
    let protocol: String
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

// MARK: - Port Scanner

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
    private let favoritesKey = "portchecker_favorites"
    private var refreshTimer: Timer?
    private var cancellables = Set<AnyCancellable>()
    
    let appVersion = "1.0.0"
    
    var bundledCliPath: String? {
        Bundle.main.path(forResource: "portchecker", ofType: nil)
    }
    
    init() {
        let defaults = UserDefaults.standard
        self.cliPath = defaults.string(forKey: cliPathKey) ?? ""
        self.showSystemServices = defaults.bool(forKey: showSystemKey)
        
        loadFavorites()
        setupAutoRefresh()
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
    
    // MARK: - Refresh
    
    func refresh() {
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = nil
        let showSystem = showSystemServices
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            
            let result = self.fetchServices(showSystem: showSystem)
            
            DispatchQueue.main.async {
                self.isLoading = false
                
                switch result {
                case .success(let services):
                    self.services = services
                    self.checkForChanges(previous: self.services, current: services)
                case .failure(let message):
                    self.services = []
                    self.errorMessage = message
                }
            }
        }
    }
    
    private func setupAutoRefresh() {
        // Auto-refresh when enabled
        Timer.publish(every: 5, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self = self,
                      UserDefaults.standard.bool(forKey: "autoRefresh"),
                      !self.isLoading else { return }
                self.refresh()
            }
            .store(in: &cancellables)
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
    
    func chooseCliPath() {
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
        // Check configured path
        if isExecutable(path: cliPath) {
            return cliPath
        }
        
        // Check bundled CLI
        if let bundled = bundledCliPath, isExecutable(path: bundled) {
            return bundled
        }
        
        // Check PATH
        if let found = findInPath("portchecker") {
            DispatchQueue.main.async {
                self.cliPath = found
            }
            return found
        }
        
        return nil
    }
    
    private func isExecutable(path: String) -> Bool {
        guard !path.isEmpty else { return false }
        return FileManager.default.isExecutableFile(atPath: path)
    }
    
    private func findInPath(_ name: String) -> String? {
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
    
    private func fetchServices(showSystem: Bool) -> Result<[PortService], String> {
        guard let cli = resolveCliPath() else {
            return .failure("CLI not found. Please install portchecker CLI or set path in Settings.")
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
                return .failure("Failed to decode CLI output")
            }
            
            let decoded = try JSONDecoder().decode([PortService].self, from: data)
            return .success(decoded)
            
        } catch let error as CLIError {
            return .failure(error.message)
        } catch {
            return .failure(error.localizedDescription)
        }
    }
    
    private func runCLI(cliPath: String, args: [String]) throws -> String {
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
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            
            defer {
                DispatchQueue.main.async {
                    self.isLoading = false
                    self.refresh()
                }
            }
            
            guard let cli = self.resolveCliPath() else {
                DispatchQueue.main.async {
                    self.errorMessage = "CLI not found"
                }
                return
            }
            
            for service in services {
                _ = try? self.runCLI(cliPath: cli, args: [
                    "stop",
                    "--pid", "\(service.pid)",
                    "--yes"
                ])
            }
        }
    }
    
    // MARK: - Favorites
    
    func loadFavorites() {
        guard let data = UserDefaults.standard.data(forKey: favoritesKey) else {
            favorites = []
            return
        }
        
        do {
            favorites = try JSONDecoder().decode([Favorite].self, from: data)
        } catch {
            favorites = []
        }
    }
    
    func saveFavorites() {
        do {
            let data = try JSONEncoder().encode(favorites)
            UserDefaults.standard.set(data, forKey: favoritesKey)
        } catch {
            print("Failed to save favorites: \(error)")
        }
    }
    
    func addFavorite(port: Int, name: String, note: String) {
        guard !favorites.contains(where: { $0.port == port }) else { return }
        
        favorites.append(Favorite(port: port, name: name, note: note))
        saveFavorites()
        refresh()
    }
    
    func removeFavorite(_ favorite: Favorite) {
        favorites.removeAll { $0.port == favorite.port }
        saveFavorites()
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
