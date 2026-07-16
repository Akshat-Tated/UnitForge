package com.unitforge.dto;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CreateJobRequest {

    @NotBlank(message = "inputType must not be blank")
    private String inputType;

    @NotBlank(message = "inputPath must not be blank")
    private String inputPath;

    /**
     * Optional module map from the analysis engine.
     * When present, the orchestrator splits it into per-module tasks
     * and pushes each to the Redis queue. When absent, the job is
     * created in QUEUED status with no tasks dispatched (Phase 1 behavior).
     */
    private JsonNode moduleMap;
}
