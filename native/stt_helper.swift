import Foundation
import Speech
import AVFoundation

struct ResultOutput: Codable {
    let status: String
    let text: String
    let error: String?
}

func printJSON(status: String, text: String, error: String? = nil) {
    let output = ResultOutput(status: status, text: text, error: error)
    if let data = try? JSONEncoder().encode(output), let jsonString = String(data: data, encoding: .utf8) {
        print(jsonString)
        fflush(stdout)
    }
}

class SpeechRecognizerManager: NSObject {
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private var audioEngine: AVAudioEngine?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    
    private var lastTranscript: String = ""
    private var isFinished = false
    private var maxTimer: Timer?
    private var silenceTimer: Timer?
    
    func run(maxSeconds: Double = 10.0, silenceTimeout: Double = 1.8) {
        guard let recognizer = speechRecognizer, recognizer.isAvailable else {
            printJSON(status: "error", text: "", error: "Speech recognizer is not available on this system.")
            exit(0)
        }

        SFSpeechRecognizer.requestAuthorization { [weak self] authStatus in
            DispatchQueue.main.async {
                guard let self = self else { return }
                if authStatus != .authorized {
                    printJSON(status: "error", text: "", error: "Speech recognition permission denied. Grant Microphone & Speech Recognition access in System Preferences -> Security & Privacy.")
                    exit(0)
                }
                self.startRecording(maxSeconds: maxSeconds, silenceTimeout: silenceTimeout)
            }
        }
        
        // Keep main runloop active
        let timeoutDate = Date().addingTimeInterval(maxSeconds + 5.0)
        while !isFinished && RunLoop.main.run(mode: .default, before: timeoutDate) {
            if Date() > timeoutDate {
                finishSession()
                break
            }
        }
    }

    private func startRecording(maxSeconds: Double, silenceTimeout: Double) {
        audioEngine = AVAudioEngine()
        guard let audioEngine = audioEngine else {
            printJSON(status: "error", text: "", error: "Failed to initialize AVAudioEngine.")
            exit(0)
        }

        let inputNode = audioEngine.inputNode
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        
        guard let recognitionRequest = recognitionRequest else {
            printJSON(status: "error", text: "", error: "Unable to create recognition request.")
            exit(0)
        }

        recognitionRequest.shouldReportPartialResults = true

        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            DispatchQueue.main.async {
                guard let self = self, !self.isFinished else { return }

                if let result = result {
                    let transcribed = result.bestTranscription.formattedString
                    if !transcribed.isEmpty {
                        self.lastTranscript = transcribed
                        self.resetSilenceTimer(timeout: silenceTimeout)
                    }
                }

                if error != nil || (result?.isFinal ?? false) {
                    self.finishSession()
                }
            }
        }

        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
        }

        do {
            audioEngine.prepare()
            try audioEngine.start()
        } catch {
            printJSON(status: "error", text: "", error: "Audio engine error: \(error.localizedDescription)")
            exit(0)
        }

        // Set overall max recording timer on main runloop
        maxTimer = Timer.scheduledTimer(withTimeInterval: maxSeconds, repeats: false) { [weak self] _ in
            self?.finishSession()
        }
    }

    private func resetSilenceTimer(timeout: Double) {
        silenceTimer?.invalidate()
        silenceTimer = Timer.scheduledTimer(withTimeInterval: timeout, repeats: false) { [weak self] _ in
            self?.finishSession()
        }
    }

    private func finishSession() {
        guard !isFinished else { return }
        isFinished = true

        maxTimer?.invalidate()
        silenceTimer?.invalidate()

        if let audioEngine = audioEngine, audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()

        let trimmedText = lastTranscript.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedText.isEmpty {
            printJSON(status: "empty", text: "")
        } else {
            printJSON(status: "success", text: trimmedText)
        }

        exit(0)
    }
}

// Arguments parsing
var maxSec: Double = 10.0
var silenceSec: Double = 1.8

let args = CommandLine.arguments
if args.count > 1, let arg1 = Double(args[1]) {
    maxSec = arg1
}
if args.count > 2, let arg2 = Double(args[2]) {
    silenceSec = arg2
}

let manager = SpeechRecognizerManager()
manager.run(maxSeconds: maxSec, silenceTimeout: silenceSec)
