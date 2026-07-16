package com.unitforge.controller;

import com.unitforge.dto.CreateJobRequest;
import com.unitforge.dto.CreateJobResponse;
import com.unitforge.dto.JobStatusResponse;
import com.unitforge.dto.TestResultResponse;
import com.unitforge.model.TestJob;
import com.unitforge.model.TestResult;
import com.unitforge.service.JobService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("${unitforge.api.base-path}")
@RequiredArgsConstructor
public class JobController {

    private final JobService jobService;

    @PostMapping("/jobs")
    public ResponseEntity<CreateJobResponse> createJob(@Valid @RequestBody CreateJobRequest request) {
        TestJob job = jobService.createJob(request.getInputType(), request.getInputPath(), request.getModuleMap());

        CreateJobResponse response = CreateJobResponse.builder()
                .jobId(job.getId())
                .status(job.getStatus().name())
                .build();

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/jobs/{id}")
    public ResponseEntity<JobStatusResponse> getJob(@PathVariable UUID id) {
        TestJob job = jobService.getJob(id);

        JobStatusResponse response = JobStatusResponse.builder()
                .id(job.getId())
                .status(job.getStatus().name())
                .inputType(job.getInputType())
                .inputPath(job.getInputPath())
                .createdAt(job.getCreatedAt())
                .updatedAt(job.getUpdatedAt())
                .build();

        return ResponseEntity.ok(response);
    }

    @GetMapping("/jobs/{id}/results")
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
}
