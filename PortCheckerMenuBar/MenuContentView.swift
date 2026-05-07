import SwiftUI

struct MenuContentView: View {
    @EnvironmentObject var scanner: PortScanner

    var body: some View {
        if scanner.isLoading {
            Text("Scanning...")
                .disabled(true)
        }

        if let error = scanner.errorMessage {
            Text(error)
                .foregroundColor(.red)
        }

        if scanner.services.isEmpty {
            Text("No ports in use")
                .disabled(true)
        } else {
            ForEach(scanner.services) { service in
                Menu {
                    Text("Port \(service.port)")
                    Text("App: \(service.app)")
                    Text("Project: \(service.project)")
                    Text("User: \(service.user)")
                    Divider()
                    Button("Stop Service") {
                        scanner.kill(service: service)
                    }
                    .disabled(service.isSystem)
                } label: {
                    Text("\(service.port) - \(service.app) - \(service.project)")
                }
            }
        }

        Divider()

        Button("Refresh") {
            scanner.refresh()
        }
        .disabled(scanner.isLoading)

        Toggle("Show System Services", isOn: $scanner.showSystemServices)
            .onChange(of: scanner.showSystemServices) { _ in
                scanner.refresh()
            }

        Button("Stop All Listed") {
            scanner.killAll()
        }
        .disabled(scanner.services.filter { !$0.isSystem }.isEmpty)

        Divider()

        Button("Set CLI Path...") {
            scanner.chooseCliPath()
        }

        Button("Quit") {
            NSApp.terminate(nil)
        }
    }
}
