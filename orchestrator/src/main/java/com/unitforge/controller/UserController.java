package com.unitforge.controller;

import com.unitforge.model.User;
import com.unitforge.repository.UserRepository;
import com.unitforge.service.EncryptionService;
import com.unitforge.service.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class UserController {

    private final UserRepository userRepository;
    private final EncryptionService encryptionService;
    private final JwtService jwtService;

    @PostMapping("/apikey")
    public ResponseEntity<Map<String, String>> saveApiKey(
            @RequestHeader("Authorization") String authHeader,
            @RequestBody Map<String, String> body) {

        String email = jwtService
            .extractEmailFromHeader(authHeader)
            .orElseThrow(() ->
                new RuntimeException("Unauthorized")
            );

        String apiKey = body.get("apiKey");
        if (apiKey == null || apiKey.isBlank()) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "apiKey is required"));
        }

        User user = userRepository.findByEmail(email)
            .orElseThrow(() ->
                new RuntimeException("User not found")
            );

        user.setGeminiApiKeyEncrypted(
            encryptionService.encrypt(apiKey)
        );
        userRepository.save(user);

        return ResponseEntity.ok(
            Map.of("message", "API key saved successfully")
        );
    }

    @GetMapping("/apikey/{email}")
    public ResponseEntity<Map<String, String>> getApiKey(
            @PathVariable String email) {
        // This endpoint is called by the test agent (internal)
        // to get the decrypted API key for a job owner
        User user = userRepository.findByEmail(email)
            .orElse(null);

        if (user == null || user.getGeminiApiKeyEncrypted() == null) {
            return ResponseEntity.notFound().build();
        }

        String decrypted = encryptionService.decrypt(
            user.getGeminiApiKeyEncrypted()
        );
        return ResponseEntity.ok(Map.of("apiKey", decrypted));
    }

    @GetMapping("/apikey/status")
    public ResponseEntity<Map<String, Object>> getApiKeyStatus(
            @RequestHeader(value = "Authorization",
                           required = false) String authHeader) {

        Optional<String> emailOpt =
            jwtService.extractEmailFromHeader(authHeader);

        if (emailOpt.isEmpty()) {
            return ResponseEntity.ok(Map.of(
                "hasKey", false,
                "message", "Not authenticated"
            ));
        }

        Optional<User> userOpt =
            userRepository.findByEmail(emailOpt.get());

        if (userOpt.isEmpty()) {
            return ResponseEntity.ok(Map.of(
                "hasKey", false,
                "message", "User not found"
            ));
        }

        User user = userOpt.get();
        boolean hasKey = user.getGeminiApiKeyEncrypted() != null
            && !user.getGeminiApiKeyEncrypted().isBlank();

        // Return masked key hint if key exists (last 4 chars only)
        String keyHint = "";
        if (hasKey) {
            try {
                String decrypted = encryptionService.decrypt(
                    user.getGeminiApiKeyEncrypted()
                );
                keyHint = "..." + decrypted.substring(
                    Math.max(0, decrypted.length() - 4)
                );
            } catch (Exception e) {
                keyHint = "...????";
            }
        }

        return ResponseEntity.ok(Map.of(
            "hasKey", hasKey,
            "keyHint", keyHint,
            "message", hasKey
                ? "API key is configured"
                : "No API key saved"
        ));
    }
}
