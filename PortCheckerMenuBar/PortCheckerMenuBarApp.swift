import SwiftUI

@main
struct PortCheckerMenuBarApp: App {
    @StateObject private var scanner = PortScanner()

    var body: some Scene {
        MenuBarExtra("Ports", systemImage: "bolt.horizontal.circle") {
            MenuContentView()
                .environmentObject(scanner)
                .onAppear {
                    scanner.refresh()
                }
        }
        .menuBarExtraStyle(.menu)
    }
}
