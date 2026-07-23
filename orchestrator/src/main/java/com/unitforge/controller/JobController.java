package com.unitforge.controller;

import com.unitforge.dto.CreateJobRequest;
import com.unitforge.dto.CreateJobResponse;
import com.unitforge.dto.JobStatusResponse;
import com.unitforge.model.TestJob;
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
@RequestMapping("${unitforge.api.base-path}")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class JobController {

    private final JobService jobService;

    @GetMapping("/jobs")
    public ResponseEntity<List<JobStatusResponse>> getAllJobs() {
        List<TestJob> jobs = jobService.getAllJobs();

        List<JobStatusResponse> response = jobs.stream()
                .map(this::toJobStatusResponse)
                .toList();

        return ResponseEntity.ok(response);
    }

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
