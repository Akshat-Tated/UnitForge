package com.unitforge.service;

import com.unitforge.model.JobStatus;
import com.unitforge.model.TestJob;
import com.unitforge.model.TestResult;
import com.unitforge.repository.TestJobRepository;
import com.unitforge.repository.TestResultRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class JobService {

    private final TestJobRepository testJobRepository;
    private final TestResultRepository testResultRepository;
    private final TaskQueueService taskQueueService;

    @Transactional
    public TestJob createJob(String inputType, String inputPath) {
        TestJob job = TestJob.builder()
                .status(JobStatus.QUEUED)
                .inputType(inputType)
                .inputPath(inputPath)
                .build();

        TestJob savedJob = testJobRepository.save(job);
        taskQueueService.pushTask(savedJob.getId().toString());
        return savedJob;
    }

    @Transactional(readOnly = true)
    public TestJob getJob(UUID jobId) {
        return testJobRepository.findById(jobId)
                .orElseThrow(() -> new IllegalArgumentException("Job not found: " + jobId));
    }

    @Transactional(readOnly = true)
    public List<TestResult> getResults(UUID jobId) {
        // Verify the job exists before fetching results
        getJob(jobId);
        return testResultRepository.findByJobId(jobId);
    }
}
