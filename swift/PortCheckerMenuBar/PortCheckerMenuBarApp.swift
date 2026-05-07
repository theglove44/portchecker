import SwiftUI

@main
struct PortCheckerMenuBarApp: App {
    @StateObject private var scanner = PortScanner()
    @AppStorage("showMenuBarBadge") private var showMenuBarBadge = true
    
    var body: some Scene {
        MenuBarExtra {
            MenuContentView()
                .environmentObject(scanner)
        } label: {
            MenuBarIcon(
                serviceCount: showMenuBarBadge ? scanner.services.count : 0,
                hasIssues: scanner.hasSecurityIssues
            )
        }
        .menuBarExtraStyle(.window)
    }
}

struct MenuBarIcon: View {
    let serviceCount: Int
    let hasIssues: Bool
    
    var body: some View {
        ZStack {
            Image(systemName: hasIssues ? "bolt.horizontal.circle.fill" : "bolt.horizontal.circle")
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(hasIssues ? .orange : .primary)
            
            if serviceCount > 0 {
                Badge(count: serviceCount)
                    .offset(x: 8, y: -8)
            }
        }
    }
}

struct Badge: View {
    let count: Int
    
    var badgeColor: Color {
        switch count {
        case 1...2: return .green
        case 3...5: return .orange
        default: return .red
        }
    }
    
    var body: some View {
        Text("\(min(count, 99))")
            .font(.system(size: 9, weight: .bold))
            .foregroundColor(.white)
            .frame(minWidth: 14, minHeight: 14)
            .background(badgeColor)
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(Color(NSColor.controlBackgroundColor), lineWidth: 1.5)
            )
    }
}
