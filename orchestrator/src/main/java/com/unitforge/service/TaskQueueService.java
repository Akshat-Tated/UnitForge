package com.unitforge.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class TaskQueueService {

    private final StringRedisTemplate redisTemplate;

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
}
