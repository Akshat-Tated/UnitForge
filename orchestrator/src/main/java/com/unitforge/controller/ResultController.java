package com.unitforge.controller;

import com.unitforge.dto.AgentResultRequest;
import com.unitforge.dto.TestResultResponse;
import com.unitforge.model.JobStatus;
import com.unitforge.model.TestResult;
import com.unitforge.repository.TestJobRepository;
import com.unitforge.repository.TestResultRepository;
import com.unitforge.service.JobService;
import com.unitforge.service.WebSocketService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("${unitforge.api.base-path}/jobs")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class ResultController {

    private final JobService jobService;
    private final WebSocketService webSocketService;
    private final TestJobRepository testJobRepository;
    private final TestResultRepository testResultRepository;

    @GetMapping("/{id}/results")
    public ResponseEntity<List<TestResultResponse>> getResults(@PathVariable UUID id) {
        List<TestResult> results = jobService.getResults(id);

        List<TestResultResponse> response = results.stream()
                .map(r -> TestResultResponse.builder()
                        .id(r.getId())
                        .jobId(r.getJobId())
                        .moduleName(r.getModuleName())
                        .passed(r.isPassed())
                        .coveragePercent(r.getCoveragePercent())
                        .generatedTestCode(r.getGeneratedTestCode())
                        .agentLog(r.getAgentLog())
                        .createdAt(r.getCreatedAt())
                        .build())
                .toList();

        return ResponseEntity.ok(response);
    }

    @PostMapping("/{id}/results")
    public ResponseEntity<?> submitResult(
            @PathVariable UUID id,
            @Valid @RequestBody AgentResultRequest request) {

        // Check job exists first — return 200 OK even if not found
        // Agent must never crash from this endpoint
        if (!testJobRepository.existsById(id)) {
            log.warn("Result posted for unknown job ID: {} — module: {}",
                    id, request.getModuleName());
            return ResponseEntity.ok(
                Map.of("message", "Job not found but result acknowledged")
            );
        }

        // Normal flow — save result
        TestResult saved = jobService.submitResult(
                id,
                request.getModuleName(),
                request.isPassed(),
                request.getCoveragePercent(),
                request.getGeneratedTestCode(),
                request.getAgentLog());

        // Save moduleInfoJson for potential rerun
        if (request.getModuleInfoJson() != null) {
            saved.setModuleInfoJson(request.getModuleInfoJson());
        }

        webSocketService.broadcastResultUpdate(saved);

        // Check if job transitioned to DONE and broadcast if so
        testJobRepository.findById(id).ifPresent(job -> {
            if (job.getStatus() == JobStatus.DONE) {
                webSocketService.broadcastJobUpdate(job);
                log.info("Job {} is now DONE", id);
            }
        });

        TestResultResponse response = TestResultResponse.builder()
                .id(saved.getId())
                .jobId(saved.getJobId())
                .moduleName(saved.getModuleName())
                .passed(saved.isPassed())
                .coveragePercent(saved.getCoveragePercent())
                .generatedTestCode(saved.getGeneratedTestCode())
                .agentLog(saved.getAgentLog())
                .createdAt(saved.getCreatedAt())
                .build();

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}

