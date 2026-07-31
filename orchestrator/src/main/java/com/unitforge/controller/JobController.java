package com.unitforge.controller;

import com.unitforge.dto.CreateJobRequest;
import com.unitforge.dto.CreateJobResponse;
import com.unitforge.dto.JobStatusResponse;
import com.unitforge.model.TestJob;
import com.unitforge.service.JobService;
import com.unitforge.service.WebSocketService;
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
@RequestMapping("${unitforge.api.base-path}")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class JobController {

    private final JobService jobService;
    private final WebSocketService webSocketService;
    private final com.unitforge.service.JwtService jwtService;
    private final com.unitforge.repository.TestJobRepository testJobRepository;

    @GetMapping("/jobs")
    public ResponseEntity<List<JobStatusResponse>> getAllJobs(
            @org.springframework.web.bind.annotation.RequestHeader(value = "Authorization", required = false)
            String authHeader) {

        java.util.Optional<String> emailOpt = jwtService.extractEmailFromHeader(authHeader);
        List<TestJob> jobs;

        if (emailOpt.isPresent()) {
            jobs = testJobRepository.findByOwnerEmailOrderByCreatedAtDesc(emailOpt.get());
        } else {
            jobs = testJobRepository.findAllByOrderByCreatedAtDesc();
        }

        List<JobStatusResponse> response = jobs.stream()
                .map(this::toJobStatusResponse)
                .toList();

        return ResponseEntity.ok(response);
    }

    @PostMapping("/jobs")
    public ResponseEntity<CreateJobResponse> createJob(
            @Valid @RequestBody CreateJobRequest request,
            @org.springframework.web.bind.annotation.RequestHeader(value = "Authorization", required = false)
            String authHeader) {
        
        String ownerEmail = jwtService.extractEmailFromHeader(authHeader).orElse("anonymous");

        TestJob job = jobService.createJob(request.getInputType(), request.getInputPath(), request.getModuleMap());
        job.setOwnerEmail(ownerEmail);
        testJobRepository.save(job);
        
        webSocketService.broadcastJobUpdate(job);

        CreateJobResponse response = CreateJobResponse.builder()
                .jobId(job.getId())
                .status(job.getStatus().name())
                .build();

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/jobs/{id}")
    public ResponseEntity<JobStatusResponse> getJob(@PathVariable UUID id) {
        TestJob job = jobService.getJob(id);
        return ResponseEntity.ok(toJobStatusResponse(job));
    }

    private JobStatusResponse toJobStatusResponse(TestJob job) {
        return JobStatusResponse.builder()
                .id(job.getId())
                .status(job.getStatus().name())
                .inputType(job.getInputType())
                .inputPath(job.getInputPath())
                .createdAt(job.getCreatedAt())
                .updatedAt(job.getUpdatedAt())
                .totalModules(job.getTotalModules())
                .build();
    }
}
