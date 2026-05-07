import Foundation

struct PortService: Codable, Identifiable {
    let pid: Int
    let port: Int
    let app: String
    let project: String
    let user: String
    let command: String
    let address: String
    let isSystem: Bool

    var id: String {
        "\(pid):\(port)"
    }

    enum CodingKeys: String, CodingKey {
        case pid
        case port
        case app
        case project
        case user
        case command
        case address
        case isSystem = "is_system"
    }
}
