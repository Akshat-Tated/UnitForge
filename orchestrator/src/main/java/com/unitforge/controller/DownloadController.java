package com.unitforge.controller;

import com.unitforge.model.TestResult;
import com.unitforge.repository.TestResultRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

@RestController
@RequestMapping("/api/jobs")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class DownloadController {

    private final TestResultRepository testResultRepository;

    @GetMapping("/{id}/download")
    public ResponseEntity<byte[]> downloadTests(@PathVariable UUID id) throws IOException {
        List<TestResult> results = testResultRepository.findByJobId(id);

        if (results.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        // Create zip in memory
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ZipOutputStream zos = new ZipOutputStream(baos)) {
            for (TestResult result : results) {
                if (result.getGeneratedTestCode() != null
                        && !result.getGeneratedTestCode().isBlank()) {
                    String fileName = "test_" + result.getModuleName() + ".py";
                    ZipEntry entry = new ZipEntry(fileName);
                    zos.putNextEntry(entry);
                    zos.write(result.getGeneratedTestCode().getBytes(StandardCharsets.UTF_8));
                    zos.closeEntry();
                }
            }
            // Add a README inside the zip
            ZipEntry readme = new ZipEntry("README.txt");
            zos.putNextEntry(readme);
            String readmeContent = "UnitForge Generated Tests\n" +
                "Job ID: " + id + "\n" +
                "Total modules: " + results.size() + "\n\n" +
                "To run: pytest test_*.py -v --cov\n";
            zos.write(readmeContent.getBytes(StandardCharsets.UTF_8));
            zos.closeEntry();
        }

        byte[] zipBytes = baos.toByteArray();

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_OCTET_STREAM);
        headers.setContentDispositionFormData("attachment",
            "unitforge-tests-" + id.toString().substring(0, 8) + ".zip");
        headers.setContentLength(zipBytes.length);

        return ResponseEntity.ok()
            .headers(headers)
            .body(zipBytes);
    }
}
