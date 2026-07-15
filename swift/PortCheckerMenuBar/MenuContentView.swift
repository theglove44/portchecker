import SwiftUI

struct MenuContentView: View {
    @EnvironmentObject var scanner: PortScanner
    @State private var hoveredService: PortService?
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HeaderView()
            
            Divider()
            
            // Services List
            ScrollView {
                VStack(alignment: .leading, spacing: 4) {
                    if scanner.isLoading {
                        LoadingView()
                    } else if let error = scanner.errorMessage {
                        ErrorView(message: error)
                    } else if scanner.groupedServices.isEmpty {
                        EmptyView()
                    } else {
                        ServicesList(
                            groupedServices: scanner.groupedServices,
                            hoveredService: $hoveredService
                        )
                    }
                }
                .padding(.vertical, 8)
            }
            .frame(maxHeight: 400)
            
            Divider()
            
            // Footer Actions
            FooterView()
        }
        .frame(width: 380)
        .onAppear {
            scanner.refresh()
        }
    }
}

// MARK: - Header
struct HeaderView: View {
    @EnvironmentObject var scanner: PortScanner
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Port Checker")
                    .font(.system(size: 15, weight: .semibold))
                
                if scanner.services.isEmpty {
                    Text("No active services")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                } else {
                    Text("\(scanner.services.count) service\(scanner.services.count == 1 ? "" : "s")")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                }
            }
            
            Spacer()
            
            if scanner.hasSecurityIssues {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                    .help("Security issues detected")
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }
}

// MARK: - Loading
struct LoadingView: View {
    var body: some View {
        HStack {
            ProgressView()
                .scaleEffect(0.7)
            Text("Scanning ports...")
                .font(.system(size: 13))
                .foregroundStyle(.secondary)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 20)
    }
}

// MARK: - Error
struct ErrorView: View {
    let message: String
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "exclamationmark.circle.fill")
                .foregroundStyle(.red)
            Text(message)
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
                .lineLimit(2)
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }
}

// MARK: - Empty
struct EmptyView: View {
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: "bolt.horizontal.circle")
                .font(.system(size: 32))
                .foregroundStyle(.secondary.opacity(0.5))
            
            Text("No ports in use")
                .font(.system(size: 13))
                .foregroundStyle(.secondary)
            
            Text("Development servers will appear here")
                .font(.system(size: 11))
                .foregroundStyle(.secondary.opacity(0.7))
        }
        .padding(.vertical, 30)
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Services List
struct ServicesList: View {
    let groupedServices: [String: [PortService]]
    @Binding var hoveredService: PortService?
    @EnvironmentObject var scanner: PortScanner
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Favorites Section
            if let favorites = groupedServices["__favorites"], !favorites.isEmpty {
                ServiceSection(
                    title: "⭐ Favorites",
                    services: favorites,
                    hoveredService: $hoveredService
                )
            }
            
            // Project Sections
            ForEach(sortedProjectKeys, id: \.self) { project in
                if let services = groupedServices[project] {
                    ServiceSection(
                        title: project == "Unknown" ? "📁 Other" : "📁 \(project)",
                        services: services,
                        hoveredService: $hoveredService
                    )
                }
            }
            
            // System Services
            if let systemServices = groupedServices["__system"], !systemServices.isEmpty {
                ServiceSection(
                    title: "🔒 System Services",
                    services: systemServices,
                    hoveredService: $hoveredService,
                    isSystem: true
                )
            }
        }
    }
    
    var sortedProjectKeys: [String] {
        groupedServices.keys
            .filter { $0 != "__favorites" && $0 != "__system" }
            .sorted { key1, key2 in
                // "Unknown" goes last
                if key1 == "Unknown" { return false }
                if key2 == "Unknown" { return true }
                return key1.lowercased() < key2.lowercased()
            }
    }
}

// MARK: - Service Section
struct ServiceSection: View {
    let title: String
    let services: [PortService]
    @Binding var hoveredService: PortService?
    var isSystem: Bool = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(.secondary)
                .padding(.horizontal, 16)
            
            ForEach(services) { service in
                ServiceRow(
                    service: service,
                    isHovered: hoveredService?.id == service.id,
                    isSystem: isSystem
                )
                .onHover { isHovered in
                    hoveredService = isHovered ? service : nil
                }
            }
        }
    }
}

// MARK: - Service Row
struct ServiceRow: View {
    let service: PortService
    let isHovered: Bool
    let isSystem: Bool
    @EnvironmentObject var scanner: PortScanner
    @State private var showingDetails = false
    @State private var showingStopConfirmation = false
    
    var portColor: Color {
        if service.isExposed {
            return .orange
        }
        if isSystem {
            return .secondary
        }
        return .green
    }
    
    var body: some View {
        HStack(spacing: 10) {
            // Port Badge
            PortBadge(
                port: service.port,
                color: portColor,
                isExposed: service.isExposed
            )
            
            // Service Info
            VStack(alignment: .leading, spacing: 1) {
                Text(service.app)
                    .font(.system(size: 13, weight: .medium))
                    .lineLimit(1)
                
                HStack(spacing: 4) {
                    Text("PID \(service.pid)")
                        .font(.system(size: 10))
                    
                    if service.isExposed {
                        Image(systemName: "network")
                            .font(.system(size: 8))
                            .foregroundStyle(.orange)
                    }
                }
                .foregroundStyle(.secondary)
            }
            
            Spacer()
            
            // Action Buttons (visible on hover)
            if isHovered && !isSystem {
                HStack(spacing: 8) {
                    Button {
                        showingDetails = true
                    } label: {
                        Image(systemName: "info.circle")
                            .font(.system(size: 13))
                    }
                    .buttonStyle(.borderless)
                    
                    Button {
                        showingStopConfirmation = true
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(.red)
                    }
                    .buttonStyle(.borderless)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .background(isHovered ? Color.accentColor.opacity(0.08) : Color.clear)
        .contentShape(Rectangle())
        .onTapGesture {
            if !isSystem {
                showingDetails = true
            }
        }
        .sheet(isPresented: $showingDetails) {
            ServiceDetailView(service: service)
                .environmentObject(scanner)
        }
        .alert("Stop \(service.app)?", isPresented: $showingStopConfirmation) {
            Button("Cancel", role: .cancel) { }
            Button("Stop", role: .destructive) { scanner.kill(service: service) }
        } message: {
            Text("This stops the process listening on port \(service.port).")
        }
    }
}

// MARK: - Port Badge
struct PortBadge: View {
    let port: Int
    let color: Color
    let isExposed: Bool
    
    var body: some View {
        Text("\(port)")
            .font(.system(size: 11, weight: .semibold, design: .monospaced))
            .foregroundStyle(color)
            .frame(width: 44, height: 22)
            .background(color.opacity(0.12))
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(color.opacity(0.3), lineWidth: 0.5)
            )
    }
}

// MARK: - Footer
struct FooterView: View {
    @EnvironmentObject var scanner: PortScanner
    
    var body: some View {
        HStack(spacing: 0) {
            Button {
                scanner.refresh()
            } label: {
                Label("Refresh", systemImage: "arrow.clockwise")
                    .font(.system(size: 12))
            }
            .buttonStyle(.borderless)
            .keyboardShortcut("r", modifiers: .command)
            .disabled(scanner.isLoading)
            
            Spacer()
            
            SettingsLink {
                Label("Settings", systemImage: "gear")
                    .font(.system(size: 12))
            }
            .buttonStyle(.borderless)
            
            Divider()
                .frame(height: 14)
                .padding(.horizontal, 8)
            
            Button {
                NSApp.terminate(nil)
            } label: {
                Label("Quit", systemImage: "power")
                    .font(.system(size: 12))
            }
            .buttonStyle(.borderless)
            .keyboardShortcut("q", modifiers: .command)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
    }
}
