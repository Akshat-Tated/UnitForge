package com.unitforge.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.NonNull;
import lombok.ToString;

import java.util.UUID;

/**
 * Transient Redis payload representing a single module task.
 * This is NOT a JPA entity — it is serialized to JSON and pushed
 * onto the Redis task queue for test-agent workers to consume.
 *
 * <p>Expected shape of {@code moduleInfoJson}:
 * <pre>{@code
 * {
 *   "name": "module_name",
 *   "type": "python|java|openapi",
 *   "functions": [...],
 *   "classes": [...],
 *   "endpoints": [...]
 * }
 * }</pre>
 *
 * // TODO: If Redis serialization switches from StringRedisTemplate to
 * //       RedisTemplate<String, ModuleTask>, add Jackson annotations
 * //       or implement Serializable.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModuleTask {

    @NonNull
    private UUID jobId;

    @NonNull
    private String moduleName;

    @NonNull
    private String moduleType;

    @NonNull
    @ToString.Exclude
    private String moduleInfoJson;
}
