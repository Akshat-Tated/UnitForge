package com.unitforge.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.unitforge.exception.JobNotFoundException;
import com.unitforge.model.JobStatus;
import com.unitforge.model.TestJob;
import com.unitforge.model.TestResult;
import com.unitforge.repository.TestJobRepository;
import com.unitforge.repository.TestResultRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class JobService {

    private final TestJobRepository testJobRepository;
    private final TestResultRepository testResultRepository;
    private final TaskQueueService taskQueueService;

    /**
     * Creates a new test generation job. If a moduleMap is provided,
     * splits it into per-module tasks, pushes them to Redis, and
     * transitions the job to RUNNING. Otherwise, falls back to
     * Phase 1 behavior (QUEUED with a simple job ID push).
     *
     * @param inputType the input source type (python, java, openapi)
     * @param inputPath path to the input source
     * @param moduleMap optional module map from the analysis engine
     * @return the persisted job
     */
    @Transactional
    public TestJob createJob(String inputType, String inputPath, JsonNode moduleMap) {
        TestJob job = TestJob.builder()
                .status(JobStatus.QUEUED)
                .inputType(inputType)
                .inputPath(inputPath)
                .build();

        TestJob savedJob = testJobRepository.save(job);

        if (moduleMap != null && moduleMap.has("modules")) {
            int taskCount = taskQueueService.pushModuleTasks(savedJob.getId(), moduleMap);
            if (taskCount > 0) {
                savedJob.setStatus(JobStatus.RUNNING);
                log.info("Job {} transitioned to RUNNING with {} task(s)", savedJob.getId(), taskCount);
            }
        } else {
            taskQueueService.pushTask(savedJob.getId().toString());
        }

        return savedJob;
    }

    @Transactional(readOnly = true)
    public TestJob getJob(UUID jobId) {
        return testJobRepository.findById(jobId)
                .orElseThrow(() -> new JobNotFoundException("Job not found: " + jobId));
    }

    @Transactional(readOnly = true)
    public List<TestResult> getResults(UUID jobId) {
        // Verify the job exists before fetching results
        getJob(jobId);
        return testResultRepository.findByJobId(jobId);
    }
}
