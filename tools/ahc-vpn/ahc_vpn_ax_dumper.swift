import Cocoa
import ApplicationServices

// A-1: 許可確認
let isTrusted = AXIsProcessTrusted()
print("=== AX Trusted: \(isTrusted) ===\n")
if !isTrusted {
    print("Error: Accessibility permission denied.")
    exit(1)
}

// A-4: オーナー手動オープン前提。openは引数(--open)がある時だけ実行
if CommandLine.arguments.contains("--open") {
    let url = URL(string: "x-apple.systempreferences:com.apple.preferences.network?VPN")!
    NSWorkspace.shared.open(url)
    Thread.sleep(forTimeInterval: 3.0)
}

guard let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == "com.apple.systempreferences" }) else {
    print("Error: System Settings not running.")
    exit(1)
}

let pid = app.processIdentifier
let appElement = AXUIElementCreateApplication(pid)

// A-3: 時間予算 (Monotonic Deadline)
let startTime = Date()
let timeBudget: TimeInterval = 30.0
AXUIElementSetMessagingTimeout(appElement, 2.0) // 個別AX呼び出しのタイムアウト

var elementCount = 0
let maxElements = 2000
let maxDepth = 12
var stopReason = "COMPLETED"

var matchedElements: [String] = []
let keywords = ["AHC DE", "AHC US", "接続", "未接続", "Connected", "Not Connected"]

func formatValue(_ valueRef: CFTypeRef?) -> String {
    guard let val = valueRef else { return "NoValue" }
    if let s = val as? String { return "Str(\"\(s)\")" }
    if let n = val as? NSNumber { return "Num(\(n))" }
    if let b = val as? Bool { return "Bool(\(b))" }
    return "Unsupported"
}

func dumpAXTree(element: AXUIElement, depth: Int, prefix: String) {
    if depth > maxDepth { stopReason = "MAX_DEPTH"; return }
    if elementCount >= maxElements { stopReason = "MAX_ELEMENTS"; return }
    if Date().timeIntervalSince(startTime) > timeBudget { stopReason = "TIMEOUT"; return }
    elementCount += 1

    var roleRef: CFTypeRef?
    var subroleRef: CFTypeRef?
    var titleRef: CFTypeRef?
    var valueRef: CFTypeRef?
    var descRef: CFTypeRef?
    var enabledRef: CFTypeRef?

    let errRole = AXUIElementCopyAttributeValue(element, kAXRoleAttribute as CFString, &roleRef)
    AXUIElementCopyAttributeValue(element, kAXSubroleAttribute as CFString, &subroleRef)
    AXUIElementCopyAttributeValue(element, kAXTitleAttribute as CFString, &titleRef)
    AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &valueRef)
    AXUIElementCopyAttributeValue(element, kAXDescriptionAttribute as CFString, &descRef)
    AXUIElementCopyAttributeValue(element, kAXEnabledAttribute as CFString, &enabledRef)

    let role = roleRef as? String ?? ""
    let title = titleRef as? String ?? ""
    let valueStr = formatValue(valueRef)
    let desc = descRef as? String ?? ""
    let enabled = formatValue(enabledRef)

    print("[D\(depth)] \(prefix)Role: \(role) | Title: \(title) | Value: \(valueStr) | Desc: \(desc) | Enabled: \(enabled)")

    let combinedText = "\(title) \(valueStr) \(desc)"
    if keywords.contains(where: { combinedText.contains($0) }) {
        matchedElements.append("[D\(depth)] Role: \(role) | Title: \(title) | Value: \(valueStr) | Desc: \(desc)")
    }

    var childrenRef: CFArray?
    AXUIElementCopyAttributeValues(element, kAXChildrenAttribute as CFString, 0, maxElements, &childrenRef)
    if let children = childrenRef as? [AXUIElement] {
        for (i, child) in children.enumerated() {
            if stopReason != "COMPLETED" { break }
            dumpAXTree(element: child, depth: depth + 1, prefix: "\(prefix)\(i).")
        }
    }
}

print("=== AX Tree Dump ===")
dumpAXTree(element: appElement, depth: 0, prefix: "")
print("\n=== Summary ===")
print("Elements: \(elementCount) / \(maxElements)")
print("Stop Reason: \(stopReason)")
print("\n=== Matched Keywords ===")
print(matchedElements.isEmpty ? "None" : matchedElements.joined(separator: "\n"))
