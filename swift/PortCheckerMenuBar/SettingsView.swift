import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var scanner: PortScanner
    @Environment(\.dismiss) private var dismiss
    
    // Settings
    @AppStorage("showSystemServices") private var showSystemServices = false
    @AppStorage("showMenuBarBadge") private var showMenuBarBadge = true
    @AppStorage("autoRefresh") private var autoRefresh = false
    @AppStorage("autoRefreshInterval") private var autoRefreshInterval = 30
    @AppStorage("showNotifications") private var showNotifications = true
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                Text("Settings")
                    .font(.system(size: 16, weight: .semibold))
                
                Spacer()
                
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 18))
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.borderless)
            }
            .padding()
            
            Divider()
            
            // Settings Form
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Display Section
                    SettingsSection(title: "Display") {
                        Toggle("Show system services", isOn: $showSystemServices)
                            .onChange(of: showSystemServices) { _ in
                                scanner.refresh()
                            }
                        
                        Toggle("Show count badge in menu bar", isOn: $showMenuBarBadge)
                        
                        Toggle("Show notifications", isOn: $showNotifications)
                    }
                    
                    // Refresh Section
                    SettingsSection(title: "Refresh") {
                        Toggle("Auto-refresh", isOn: $autoRefresh)
                        
                        if autoRefresh {
                            HStack {
                                Text("Interval:")
                                Picker("", selection: $autoRefreshInterval) {
                                    Text("10 seconds").tag(10)
                                    Text("30 seconds").tag(30)
                                    Text("1 minute").tag(60)
                                    Text("5 minutes").tag(300)
                                }
                                .pickerStyle(.segmented)
                            }
                        }
                    }
                    
                    // CLI Section
                    SettingsSection(title: "CLI Path") {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(scanner.cliPath.isEmpty ? "Using bundled CLI" : scanner.cliPath)
                                    .font(.system(size: 11, design: .monospaced))
                                    .lineLimit(1)
                                    .truncationMode(.middle)
                                
                                Spacer()
                                
                                Button {
                                    scanner.chooseCliPath()
                                } label: {
                                    Text("Change...")
                                }
                                .controlSize(.small)
                            }
                            
                            if scanner.cliPath.isEmpty {
                                Text("Using bundled CLI at \(scanner.bundledCliPath ?? "Not found")")
                                    .font(.system(size: 10))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    
                    // Favorites Section
                    SettingsSection(title: "Favorites") {
                        if scanner.favorites.isEmpty {
                            Text("No favorites configured")
                                .font(.system(size: 12))
                                .foregroundStyle(.secondary)
                        } else {
                            VStack(alignment: .leading, spacing: 6) {
                                ForEach(scanner.favorites) { fav in
                                    HStack {
                                        Text("\(fav.port)")
                                            .font(.system(size: 12, design: .monospaced))
                                            .frame(width: 50, alignment: .leading)
                                        
                                        Text(fav.name)
                                            .font(.system(size: 12))
                                        
                                        Spacer()
                                        
                                        Button {
                                            scanner.removeFavorite(fav)
                                        } label: {
                                            Image(systemName: "xmark")
                                                .font(.system(size: 10))
                                        }
                                        .buttonStyle(.borderless)
                                    }
                                }
                            }
                        }
                        
                        Divider()
                        
                        Button {
                            showingAddFavorite = true
                        } label: {
                            Label("Add Favorite", systemImage: "plus")
                        }
                        .controlSize(.small)
                    }
                    
                    // About Section
                    SettingsSection(title: "About") {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Port Checker")
                                    .font(.system(size: 13, weight: .medium))
                                Text("Version \(scanner.appVersion)")
                                    .font(.system(size: 11))
                                    .foregroundStyle(.secondary)
                            }
                            
                            Spacer()
                            
                            Button {
                                NSWorkspace.shared.open(URL(string: "https://github.com/portchecker/portchecker")!)
                            } label: {
                                Image(systemName: "arrow.up.forward")
                            }
                        }
                    }
                }
                .padding()
            }
        }
        .frame(width: 400, height: 500)
        .sheet(isPresented: $showingAddFavorite) {
            AddFavoriteView { port, name, note in
                scanner.addFavorite(port: port, name: name, note: note)
            }
        }
        .onAppear {
            scanner.loadFavorites()
        }
    }
    
    @State private var showingAddFavorite = false
}

// MARK: - Settings Section
struct SettingsSection<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.secondary)
            
            VStack(alignment: .leading, spacing: 10) {
                content
            }
        }
    }
}

// MARK: - Add Favorite View
struct AddFavoriteView: View {
    let onAdd: (Int, String, String) -> Void
    @Environment(\.dismiss) private var dismiss
    
    @State private var port = ""
    @State private var name = ""
    @State private var note = ""
    
    var isValid: Bool {
        guard let portNum = Int(port), portNum > 0 && portNum < 65536 else { return false }
        return !name.isEmpty
    }
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Add Favorite")
                .font(.system(size: 16, weight: .semibold))
            
            Form {
                HStack {
                    Text("Port:")
                        .frame(width: 60, alignment: .trailing)
                    TextField("8080", text: $port)
                        .textFieldStyle(.roundedBorder)
                }
                
                HStack {
                    Text("Name:")
                        .frame(width: 60, alignment: .trailing)
                    TextField("My Service", text: $name)
                        .textFieldStyle(.roundedBorder)
                }
                
                HStack {
                    Text("Note:")
                        .frame(width: 60, alignment: .trailing)
                    TextField("Optional", text: $note)
                        .textFieldStyle(.roundedBorder)
                }
            }
            
            HStack {
                Button("Cancel") {
                    dismiss()
                }
                
                Spacer()
                
                Button("Add") {
                    if let portNum = Int(port) {
                        onAdd(portNum, name, note)
                        dismiss()
                    }
                }
                .disabled(!isValid)
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding()
        .frame(width: 320)
    }
}
