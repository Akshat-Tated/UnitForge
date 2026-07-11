package com.unitforge.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class JobStatusResponse {

    private UUID id;
    private String status;
    private String inputType;
    private String inputPath;
    private Instant createdAt;
    private Instant updatedAt;
}
