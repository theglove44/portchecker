// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "PortChecker",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "PortChecker", targets: ["PortChecker"]),
    ],
    targets: [
        .executableTarget(
            name: "PortChecker",
            path: "swift/PortCheckerMenuBar",
            exclude: ["Info.plist", "README.md", "PortCheckerMenuBar.xcassets"],
            resources: [.copy("Resources")]
        ),
    ]
)
