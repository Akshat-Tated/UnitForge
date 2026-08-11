package com.unitforge.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;

@Service
public class EncryptionService {

    @Value("${unitforge.encryption.key:unitforge-default-enc-key-32ch}")
    private String encryptionKey;

    private static final String ALGORITHM = "AES/CBC/PKCS5Padding";

    public String encrypt(String plainText) {
        try {
            byte[] keyBytes = Arrays.copyOf(
                encryptionKey.getBytes(StandardCharsets.UTF_8), 32
            );
            SecretKeySpec secretKey = new SecretKeySpec(keyBytes, "AES");
            Cipher cipher = Cipher.getInstance(ALGORITHM);
            byte[] iv = new byte[16];
            new SecureRandom().nextBytes(iv);
            cipher.init(Cipher.ENCRYPT_MODE, secretKey,
                new IvParameterSpec(iv));
            byte[] encrypted = cipher.doFinal(
                plainText.getBytes(StandardCharsets.UTF_8)
            );
            // Prepend IV to encrypted bytes
            byte[] combined = new byte[iv.length + encrypted.length];
            System.arraycopy(iv, 0, combined, 0, iv.length);
            System.arraycopy(encrypted, 0, combined, iv.length, encrypted.length);
            return Base64.getEncoder().encodeToString(combined);
        } catch (Exception e) {
            throw new RuntimeException("Encryption failed", e);
        }
    }

    public String decrypt(String encryptedText) {
        try {
            byte[] keyBytes = Arrays.copyOf(
                encryptionKey.getBytes(StandardCharsets.UTF_8), 32
            );
            SecretKeySpec secretKey = new SecretKeySpec(keyBytes, "AES");
            byte[] combined = Base64.getDecoder().decode(encryptedText);
            byte[] iv = Arrays.copyOf(combined, 16);
            byte[] encrypted = Arrays.copyOfRange(combined, 16, combined.length);
            Cipher cipher = Cipher.getInstance(ALGORITHM);
            cipher.init(Cipher.DECRYPT_MODE, secretKey,
                new IvParameterSpec(iv));
            return new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException("Decryption failed", e);
        }
    }
}
