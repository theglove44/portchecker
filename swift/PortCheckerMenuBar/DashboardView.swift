import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var scanner: PortScanner
    @State private var selection: PortService.ID?

    private var selectedService: PortService? {
        scanner.services.first { $0.id == selection }
    }

    var body: some View {
        NavigationSplitView {
            List(selection: $selection) {
                ForEach(scanner.sidebarGroups) { group in
                    Section(group.name) {
                        ForEach(group.services) { service in
                            ServiceSidebarRow(service: service)
                                .tag(service.id)
                        }
                    }
                }
            }
            .listStyle(.sidebar)
            .navigationTitle("Port Checker")
        } detail: {
            if let selectedService {
                ServiceDetailView(service: selectedService)
                    .environmentObject(scanner)
            } else if scanner.isLoading {
                ProgressView("Scanning ports…")
            } else if let error = scanner.errorMessage {
                ContentUnavailableView("Could not scan ports", systemImage: "exclamationmark.triangle", description: Text(error))
            } else {
                ContentUnavailableView("No service selected", systemImage: "network")
            }
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Refresh", systemImage: "arrow.clockwise") { scanner.refresh() }
                    .keyboardShortcut("r", modifiers: .command)
                    .disabled(scanner.isLoading)
            }
        }
        .onAppear { scanner.refresh() }
    }
}

private struct ServiceSidebarRow: View {
    let service: PortService

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: service.isExposed ? "exclamationmark.triangle.fill" : "circle.fill")
                .foregroundStyle(service.isExposed ? .orange : (service.isSystem ? .secondary : .green))
                .font(.caption)
            VStack(alignment: .leading, spacing: 2) {
                Text(service.app.isEmpty ? service.command : service.app)
                    .lineLimit(1)
                Text("localhost:\(service.port) · PID \(service.pid)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
