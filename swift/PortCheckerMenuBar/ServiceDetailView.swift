import SwiftUI

struct ServiceDetailView: View {
    let service: PortService
    @EnvironmentObject var scanner: PortScanner
    @Environment(\.dismiss) private var dismiss
    @State private var showingStopConfirmation = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(service.app)
                        .font(.system(size: 18, weight: .semibold))
                    Text("Port \(service.port)")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
                
                PortBadge(
                    port: service.port,
                    color: service.isExposed ? .orange : .green,
                    isExposed: service.isExposed
                )
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Details
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Process Info Section
                    DetailSection(title: "Process") {
                        DetailRow(label: "Command", value: service.command)
                        DetailRow(label: "PID", value: "\(service.pid)")
                        DetailRow(label: "User", value: service.user)
                    }
                    
                    // Network Section
                    DetailSection(title: "Network") {
                        DetailRow(label: "Address", value: service.address)
                        DetailRow(label: "Binding", value: service.isExposed ? "Exposed" : "Local only")
                        
                        if service.isExposed, let reason = service.exposureReason {
                            DetailRow(label: "Exposure", value: reason)
                                .foregroundStyle(.orange)
                        }
                    }
                    
                    // Project Section
                    DetailSection(title: "Project") {
                        DetailRow(label: "Directory", value: service.project)
                        
                        if service.project != "Unknown" && service.project != "Unavailable" {
                            Button {
                                revealInFinder()
                            } label: {
                                Label("Reveal in Finder", systemImage: "folder")
                            }
                            .buttonStyle(.link)
                        }
                    }
                    
                    // Security Section
                    if !service.securityIssues.isEmpty {
                        DetailSection(title: "Security") {
                            ForEach(service.securityIssues, id: \.self) { issue in
                                SecurityIssueRow(severity: issue.severity, message: issue.message)
                            }
                        }
                    }
                    
                    // Fingerprint Section
                    if let fingerprint = service.fingerprint {
                        DetailSection(title: "Service Detection") {
                            DetailRow(label: "Service", value: fingerprint.service)
                            if !fingerprint.version.isEmpty {
                                DetailRow(label: "Version", value: fingerprint.version)
                            }
                            if !fingerprint.transportProtocol.isEmpty {
                                DetailRow(label: "Protocol", value: fingerprint.transportProtocol)
                            }
                        }
                    }
                }
                .padding()
            }
            
            Divider()
            
            // Actions
            HStack {
                Button {
                    dismiss()
                } label: {
                    Text("Close")
                }
                .keyboardShortcut(.escape, modifiers: [])
                
                Spacer()
                
                Button {
                    copyCommand()
                } label: {
                    Label("Copy Command", systemImage: "doc.on.doc")
                }

                Button {
                    copyEndpoint()
                } label: {
                    Label("Copy Address", systemImage: "link")
                }

                Button {
                    NSWorkspace.shared.open(URL(string: "http://localhost:\(service.port)")!)
                } label: {
                    Label("Open", systemImage: "safari")
                }
                
                if !service.isSystem {
                    Button {
                        showingStopConfirmation = true
                    } label: {
                        Label("Stop Service", systemImage: "stop.fill")
                            .foregroundStyle(.red)
                    }
                    .keyboardShortcut(.return, modifiers: .command)
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
        }
        .frame(width: 420, height: 500)
        .alert("Stop Service?", isPresented: $showingStopConfirmation) {
            Button("Cancel", role: .cancel) { }
            Button("Stop", role: .destructive) {
                scanner.kill(service: service)
                dismiss()
            }
        } message: {
            Text("This will stop \(service.app) on port \(service.port).")
        }
    }
    
    private func copyCommand() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(service.command, forType: .string)
    }

    private func copyEndpoint() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString("localhost:\(service.port)", forType: .string)
    }
    
    private func revealInFinder() {
        // Try to find the working directory from process info
        // This is a simplified version - real implementation would use lsof
    }
}

// MARK: - Detail Section
struct DetailSection<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(.secondary)
                .textCase(.uppercase)
            
            VStack(alignment: .leading, spacing: 6) {
                content
            }
            .padding(12)
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)
        }
    }
}

// MARK: - Detail Row
struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack(alignment: .top) {
            Text(label)
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
                .frame(width: 80, alignment: .leading)
            
            Text(value)
                .font(.system(size: 12, design: .monospaced))
                .lineLimit(nil)
                .textSelection(.enabled)
            
            Spacer()
        }
    }
}

// MARK: - Security Issue Row
struct SecurityIssueRow: View {
    let severity: String
    let message: String
    
    var color: Color {
        switch severity {
        case "HIGH": return .red
        case "MEDIUM": return .orange
        default: return .blue
        }
    }
    
    var icon: String {
        switch severity {
        case "HIGH": return "exclamationmark.octagon.fill"
        case "MEDIUM": return "exclamationmark.triangle.fill"
        default: return "info.circle.fill"
        }
    }
    
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .foregroundStyle(color)
                .font(.system(size: 12))
            
            Text(message)
                .font(.system(size: 12))
                .foregroundStyle(color)
            
            Spacer()
        }
    }
}
