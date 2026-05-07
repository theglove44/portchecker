import AppKit
import Foundation
import SwiftUI

final class PortScanner: ObservableObject {
    @Published var services: [PortService] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var showSystemServices: Bool {
        didSet {
            UserDefaults.standard.set(showSystemServices, forKey: showSystemKey)
        }
    }
    @Published private(set) var cliPath: String {
        didSet {
            UserDefaults.standard.set(cliPath, forKey: cliPathKey)
        }
    }

    private let cliPathKey = "portchecker_cliPath"
    private let showSystemKey = "portchecker_showSystem"

    init() {
        let defaults = UserDefaults.standard
        self.cliPath = defaults.string(forKey: cliPathKey) ?? ""
        self.showSystemServices = defaults.bool(forKey: showSystemKey)
    }

    func refresh() {
        if isLoading {
            return
        }

        isLoading = true
        errorMessage = nil
        let showSystem = showSystemServices

        DispatchQueue.global(qos: .userInitiated).async {
            let result = self.fetchServices(showSystem: showSystem)
            DispatchQueue.main.async {
                self.isLoading = false
                switch result {
                case .success(let services):
                    self.services = services
                case .failure(let message):
                    self.services = []
                    self.errorMessage = message
                }
            }
        }
    }

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

    func kill(service: PortService) {
        if service.isSystem {
            return
        }

        let title = "Stop \(service.app)?"
        let message = "Port \(service.port) in \(service.project) (PID \(service.pid))."
        guard confirmAction(title: title, message: message, confirmTitle: "Stop") else {
            return
        }

        runStop(services: [service])
    }

    func killAll() {
        let targets = services.filter { !$0.isSystem }
        if targets.isEmpty {
            return
        }

        let title = "Stop \(targets.count) services?"
        let message = "This will stop all listed non-system services."
        guard confirmAction(title: title, message: message, confirmTitle: "Stop All") else {
            return
        }

        runStop(services: targets)
    }

    private func runStop(services: [PortService]) {
        isLoading = true
        errorMessage = nil

        DispatchQueue.global(qos: .userInitiated).async {
            guard let cli = self.resolveCliPath() else {
                DispatchQueue.main.async {
                    self.isLoading = false
                    self.errorMessage = "CLI not found. Use 'Set CLI Path...'"
                }
                return
            }

            for service in services {
                _ = try? self.runCLI(cliPath: cli, args: [
                    "stop",
                    "--pid",
                    "\(service.pid)",
                    "--yes"
                ])
            }

            DispatchQueue.main.async {
                self.isLoading = false
                self.refresh()
            }
        }
    }

    private func fetchServices(showSystem: Bool) -> Result<[PortService], String> {
        guard let cli = resolveCliPath() else {
            return .failure("CLI not found. Use 'Set CLI Path...'")
        }

        var args = ["scan", "--json"]
        if showSystem {
            args.append("--show-system")
        }

        do {
            let output = try runCLI(cliPath: cli, args: args)
            let trimmed = output.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.isEmpty {
                return .success([])
            }
            guard let data = trimmed.data(using: .utf8) else {
                return .failure("Failed to decode CLI output.")
            }
            let decoded = try JSONDecoder().decode([PortService].self, from: data)
            let sorted = decoded.sorted { $0.port < $1.port }
            return .success(sorted)
        } catch {
            return .failure(error.localizedDescription)
        }
    }

    private func resolveCliPath() -> String? {
        if isExecutable(path: cliPath) {
            return cliPath
        }

        if let found = findInPath("portchecker") {
            DispatchQueue.main.async {
                self.cliPath = found
            }
            return found
        }

        return nil
    }

    private func isExecutable(path: String) -> Bool {
        if path.isEmpty {
            return false
        }
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
        if process.terminationStatus != 0 {
            return nil
        }

        let data = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let path = String(data: data, encoding: .utf8)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if let path, !path.isEmpty {
            return path
        }
        return nil
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
            throw CLIError(message: "Failed to run CLI at \(cliPath).")
        }

        process.waitUntilExit()

        let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
        let output = String(data: outputData, encoding: .utf8) ?? ""

        if process.terminationStatus != 0 {
            let errorText = String(data: errorData, encoding: .utf8) ?? ""
            let message = errorText.trimmingCharacters(in: .whitespacesAndNewlines)
            if message.isEmpty {
                throw CLIError(message: "CLI exited with status \(process.terminationStatus).")
            }
            throw CLIError(message: message)
        }

        return output
    }

    private func confirmAction(title: String, message: String, confirmTitle: String) -> Bool {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.alertStyle = .warning
        alert.addButton(withTitle: confirmTitle)
        alert.addButton(withTitle: "Cancel")
        return alert.runModal() == .alertFirstButtonReturn
    }

    private struct CLIError: LocalizedError {
        let message: String

        var errorDescription: String? {
            message
        }
    }
}
