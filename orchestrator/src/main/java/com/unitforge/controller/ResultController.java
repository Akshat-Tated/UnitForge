package com.unitforge.controller;

import com.unitforge.dto.AgentResultRequest;
import com.unitforge.dto.TestResultResponse;
import com.unitforge.model.TestResult;
import com.unitforge.service.JobService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
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
import java.util.UUID;

@RestController
@RequestMapping("${unitforge.api.base-path}/jobs")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class ResultController {

    private final JobService jobService;

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
    public ResponseEntity<TestResultResponse> submitResult(
            @PathVariable UUID id,
            @Valid @RequestBody AgentResultRequest request) {

        TestResult saved = jobService.submitResult(
                id,
                request.getModuleName(),
                request.isPassed(),
                request.getCoveragePercent(),
                request.getGeneratedTestCode(),
                request.getAgentLog());

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
