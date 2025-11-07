//
//  CameraController.swift
//  PingCamera
//
//  Created by Codex on 8/11/2025.
//

import AVFoundation
import Foundation

@MainActor
final class CameraController: ObservableObject {
    @Published private(set) var authorizationStatus: AVAuthorizationStatus
    @Published var errorMessage: String?

    let session = AVCaptureSession()

    private var sessionConfigured = false

    init() {
        authorizationStatus = AVCaptureDevice.authorizationStatus(for: .video)
        if authorizationStatus == .authorized {
            configureSessionIfNeeded()
        }
    }

    func requestAccessIfNeeded() {
        let currentStatus = AVCaptureDevice.authorizationStatus(for: .video)
        authorizationStatus = currentStatus
        if currentStatus == .notDetermined {
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                guard let self else { return }
                Task { @MainActor in
                    self.authorizationStatus = granted ? .authorized : .denied
                    if granted {
                        self.configureSessionIfNeeded()
                    } else {
                        self.errorMessage = "需要摄像头权限才能显示画面。"
                    }
                }
            }
            return
        }

        if authorizationStatus == .authorized {
            configureSessionIfNeeded()
        } else if authorizationStatus == .restricted {
            errorMessage = "系统限制了摄像头访问。"
        }
    }

    func refreshAuthorizationStatus() {
        authorizationStatus = AVCaptureDevice.authorizationStatus(for: .video)
        if authorizationStatus == .authorized {
            configureSessionIfNeeded()
        }
    }

    private func configureSessionIfNeeded() {
        guard !sessionConfigured else { return }
        sessionConfigured = true

        session.beginConfiguration()
        session.sessionPreset = .high

        guard let device = AVCaptureDevice.default(for: .video) else {
            errorMessage = "找不到可用摄像头。"
            session.commitConfiguration()
            sessionConfigured = false
            return
        }

        do {
            let input = try AVCaptureDeviceInput(device: device)
            if session.canAddInput(input) {
                session.addInput(input)
            } else {
                throw CameraControllerError.cannotAddInput
            }
        } catch {
            errorMessage = "摄像头初始化失败：\(error.localizedDescription)"
            session.commitConfiguration()
            sessionConfigured = false
            return
        }

        session.commitConfiguration()

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }
            if !self.session.isRunning {
                self.session.startRunning()
            }
        }
    }

    nonisolated(unsafe) func stopSession() {
        let session = session
        DispatchQueue.global(qos: .userInitiated).async {
            if session.isRunning {
                session.stopRunning()
            }
        }
    }

    deinit {
        stopSession()
    }
}

private enum CameraControllerError: Error {
    case cannotAddInput
}
