package playground.shutdown.stage6.chain;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.Objects;

/**
 * 사용자별 대기열. 같은 사용자의 요청은 한 번에 하나만 브로커로 보낸다.
 *
 * <pre>
 * 1. Redis list(사용자 대기열) 끝에 요청을 넣는다        RPUSH
 * 2. 내가 맨 앞이면 = 이 사용자의 처리 중인 요청이 없으면  LINDEX 0
 * 3. Rabbit 큐에 발행한다. 맨 앞이 아니면 앞 요청이 끝난 뒤 다음 차례로 올라간다 (그 부분은 이 stage 범위 밖)
 * </pre>
 */
public class UserJobQueue {

    public static final String RABBIT_QUEUE = "jobs";

    private final StringRedisTemplate redis;
    private final RabbitTemplate rabbit;

    public UserJobQueue(StringRedisTemplate redis, RabbitTemplate rabbit) {
        this.redis = redis;
        this.rabbit = rabbit;
    }

    public void enqueue(JobEvents.Created created) {
        String key = key(created.userId());
        String request = String.valueOf(created.requestId());

        Step.run("redis push", () -> redis.opsForList().rightPush(key, request));
        String head = Step.run("redis head", () -> redis.opsForList().index(key, 0));
        if (Objects.equals(head, request)) {
            Step.run("rabbit publish", () -> rabbit.convertAndSend("", RABBIT_QUEUE, request));
        }
    }

    public static String key(String userId) {
        return "user-queue:" + userId;
    }
}
