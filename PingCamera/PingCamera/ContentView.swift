//
//  ContentView.swift
//  PingCamera
//
//  Created by Qiqi Zhou on 8/11/2025.
//

import AppKit
import SwiftUI

struct ContentView: View {
    @StateObject private var cameraController = CameraController()
    @State private var isPinnedOnTop = true
    @State private var isMirrored = false
    @State private var hostingWindow: NSWindow?
    @Binding var showTitleBar: Bool

    var body: some View {
        ZStack {
            switch cameraController.authorizationStatus {
            case .authorized:
                CameraPreviewView(session: cameraController.session)
                    .scaleEffect(x: isMirrored ? -1 : 1, y: 1)
                    .background(Color.black)
                    .clipped()

            case .denied, .restricted:
                PermissionPromptView(
                    message: "请在系统设置 -> 隐私与安全性 -> 摄像头 中允许 PingCamera 使用摄像头。",
                    openSettingsAction: openCameraPrivacySettings,
                    refreshAction: cameraController.refreshAuthorizationStatus
                )

            case .notDetermined:
                ProgressView("正在请求摄像头权限…")
                    .font(.headline)

            @unknown default:
                ProgressView()
            }

            if let message = cameraController.errorMessage {
                Text(message)
                    .font(.callout)
                    .multilineTextAlignment(.center)
                    .padding(12)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
            }
        }
        .overlay(alignment: .topTrailing) {
            ControlBar(
                isPinnedOnTop: $isPinnedOnTop,
                isMirrored: $isMirrored
            )
            .padding(.top, 6)
            .padding(.trailing, 6)
        }
        .frame(minWidth: 80, minHeight: 60)
        .background(Color.black)
        .background(WindowReader(window: $hostingWindow))
        .onChange(of: hostingWindow) { window in
            configure(window: window)
        }
        .onChange(of: isPinnedOnTop) { _ in
            updateWindowLevel()
        }
        .onChange(of: showTitleBar) { _ in
            updateTitleBarVisibility()
        }
        .task {
            cameraController.requestAccessIfNeeded()
        }
    }

    private func configure(window: NSWindow?) {
        guard let window else { return }
        window.title = "PingCamera"
        window.isOpaque = false
        window.backgroundColor = .clear
        window.isMovableByWindowBackground = true
        window.collectionBehavior.insert(.canJoinAllSpaces)
        window.collectionBehavior.insert(.fullScreenNone)
        window.minSize = NSSize(width: 80, height: 60)
        updateWindowLevel()
        updateTitleBarVisibility()
    }

    private func updateWindowLevel() {
        guard let window = hostingWindow else { return }
        window.level = isPinnedOnTop ? .floating : .normal
    }
    
    private func updateTitleBarVisibility() {
        guard let window = hostingWindow else { return }
        if showTitleBar {
            window.titleVisibility = .visible
            window.titlebarAppearsTransparent = false
            window.styleMask.insert(.titled)
            window.styleMask.insert(.closable)
            window.styleMask.insert(.miniaturizable)
        } else {
            window.titleVisibility = .hidden
            window.titlebarAppearsTransparent = true
            window.styleMask.remove(.titled)
            window.styleMask.remove(.closable)
            window.styleMask.remove(.miniaturizable)
        }
    }

    private func openCameraPrivacySettings() {
        guard let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera") else { return }
        NSWorkspace.shared.open(url)
    }
}

private struct ControlBar: View {
    @Binding var isPinnedOnTop: Bool
    @Binding var isMirrored: Bool

    var body: some View {
        HStack(spacing: 6) {
            IconButton(
                systemImage: isPinnedOnTop ? "pin.fill" : "pin",
                action: { isPinnedOnTop.toggle() },
                help: isPinnedOnTop ? "取消置顶" : "保持窗口悬浮在最前面"
            )

            IconButton(
                systemImage: isMirrored ? "arrow.left.and.right.righttriangle.left.righttriangle.right" : "arrow.left.arrow.right",
                action: { withAnimation(.easeInOut(duration: 0.12)) { isMirrored.toggle() } },
                help: isMirrored ? "恢复正常方向" : "镜像翻转画面"
            )
        }
        .buttonStyle(.plain)
        .foregroundStyle(.primary)
        .padding(.vertical, 4)
        .padding(.horizontal, 6)
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(.thinMaterial)
                .opacity(0.55)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(.white.opacity(0.15), lineWidth: 0.5)
        )
        .shadow(color: .black.opacity(0.18), radius: 8, y: 3)
    }

    private struct IconButton: View {
        let systemImage: String
        let action: () -> Void
        let help: String

        var body: some View {
            Button(action: action) {
                Image(systemName: systemImage)
                    .font(.system(size: 12, weight: .medium))
                    .frame(width: 22, height: 22)
            }
            .help(help)
        }
    }
}

private struct PermissionPromptView: View {
    let message: String
    let openSettingsAction: () -> Void
    let refreshAction: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "video.slash.fill")
                .font(.system(size: 42))
                .foregroundColor(.secondary)

            Text("需要摄像头权限")
                .font(.headline)

            Text(message)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            HStack {
                Button("打开系统设置", action: openSettingsAction)
                Button("我已授权，刷新", action: refreshAction)
            }
            .buttonStyle(.bordered)
        }
        .padding(24)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}

private struct WindowReader: NSViewRepresentable {
    @Binding var window: NSWindow?

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            self.window = view.window
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        DispatchQueue.main.async {
            self.window = nsView.window
        }
    }
}

#Preview {
    ContentView(showTitleBar: .constant(false))
}
