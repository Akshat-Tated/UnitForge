package com.unitforge.service;

import com.unitforge.model.TestJob;
import com.unitforge.model.TestResult;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class WebSocketService {

    private final SimpMessagingTemplate messagingTemplate;

    public void broadcastJobUpdate(TestJob job) {
        messagingTemplate.convertAndSend("/topic/jobs", job);
        messagingTemplate.convertAndSend(
            "/topic/jobs/" + job.getId(), job
        );
    }

    public void broadcastResultUpdate(TestResult result) {
        messagingTemplate.convertAndSend(
            "/topic/jobs/" + result.getJobId() + "/results", result
        );
    }
}
