package com.unitforge.controller;

import com.unitforge.model.User;
import com.unitforge.repository.UserRepository;
import com.unitforge.service.EncryptionService;
import com.unitforge.service.JwtService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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

@Slf4j
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

    @org.springframework.beans.factory.annotation.Value("${unitforge.agent-token}")
    private String expectedAgentToken;

    @GetMapping("/apikey/lookup/{email}")
    public ResponseEntity<Map<String, String>> getApiKey(
            @RequestHeader(value = "Authorization", required = false) String authHeader,
            @PathVariable String email) {
        
        logger.info(
            "Agent API-key lookup authentication received: "
            + (authHeader != null ? "Authorization header present" : "missing")
        );
        // Ensure request comes from the trusted test agent
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            return ResponseEntity.status(401).build();
        }
        String providedToken = authHeader.substring(7);
        logger.info("token present = true");
        if (!providedToken.equals(expectedAgentToken)) {
            return ResponseEntity.status(403).build();
        }

        log.info("API key fetch request for email: {}", email);

        Optional<User> userOpt = userRepository.findByEmail(email);

        if (userOpt.isEmpty()) {
            log.warn("No user found for email: {}", email);
            return ResponseEntity.notFound().build();
        }

        User user = userOpt.get();
        if (user.getGeminiApiKeyEncrypted() == null
                || user.getGeminiApiKeyEncrypted().isBlank()) {
            log.info("User found but no key saved: {}", email);
            return ResponseEntity.notFound().build();
        }

        String decrypted = encryptionService.decrypt(
            user.getGeminiApiKeyEncrypted()
        );
        log.info("Returning API key for: {}", email);
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
                "keyHint", "",
                "message", "Not authenticated"
            ));
        }

        Optional<User> userOpt =
            userRepository.findByEmail(emailOpt.get());

        if (userOpt.isEmpty()) {
            return ResponseEntity.ok(Map.of(
                "hasKey", false,
                "keyHint", "",
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
    @GetMapping("/apikey/debug/fingerprint")
    public ResponseEntity<Map<String, String>> getAgentTokenFingerprint() {
        try {
            java.security.MessageDigest digest = java.security.MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(expectedAgentToken.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder(2 * hash.length);
            for (int i = 0; i < hash.length; i++) {
                String hex = Integer.toHexString(0xff & hash[i]);
                if(hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            return ResponseEntity.ok(Map.of("fingerprint", hexString.toString().substring(0, 8)));
        } catch (Exception e) {
            return ResponseEntity.status(500).build();
        }
    }
}
