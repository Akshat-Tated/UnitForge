package com.unitforge.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.unitforge.dto.ModuleTask;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class TaskQueueService {

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;

    @Value("${unitforge.queue.task-key}")
    private String taskQueueKey;

    /**
     * Pushes a task (job ID) onto the Redis task queue for worker consumption.
     *
     * @param taskPayload the serialized task identifier (job UUID)
     */
    public void pushTask(String taskPayload) {
        redisTemplate.opsForList().rightPush(taskQueueKey, taskPayload);
    }

    /**
     * Splits a module map into individual module tasks and pushes each
     * as a JSON message onto the Redis task queue.
     *
     * @param jobId     the parent job UUID
     * @param moduleMap the full module map from the analysis engine
     * @return the number of tasks pushed
     */
    public int pushModuleTasks(UUID jobId, JsonNode moduleMap) {
        JsonNode modules = moduleMap.get("modules");
        if (modules == null || !modules.isArray()) {
            log.warn("No 'modules' array found in moduleMap for job {}", jobId);
            return 0;
        }

        int count = 0;
        for (JsonNode module : modules) {
            String moduleName = module.has("name") ? module.get("name").asText() : "unknown";
            String moduleType = module.has("type") ? module.get("type").asText() : "unknown";

            ModuleTask task = ModuleTask.builder()
                    .jobId(jobId)
                    .moduleName(moduleName)
                    .moduleType(moduleType)
                    .moduleInfoJson(module.toString())
                    .build();

            try {
                String taskJson = objectMapper.writeValueAsString(task);
                redisTemplate.opsForList().rightPush(taskQueueKey, taskJson);
                count++;
                log.debug("Pushed task for module '{}' (job {})", moduleName, jobId);
            } catch (JsonProcessingException e) {
                log.error("Failed to serialize task for module '{}' (job {}): {}",
                        moduleName, jobId, e.getMessage());
            }
        }

        int expectedCount = modules.size();
        if (count < expectedCount) {
            log.warn("Partial push for job {}: pushed {}/{} task(s)", jobId, count, expectedCount);
        } else {
            log.info("Pushed {}/{} module task(s) for job {}", count, expectedCount, jobId);
        }
        return count;
    }
}
