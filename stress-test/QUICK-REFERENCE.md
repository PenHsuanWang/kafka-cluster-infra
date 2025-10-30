# Remote Testing Quick Reference

## 3 Ways to Test Remote Clusters

### 1️⃣ Helper Script (Easiest)
```bash
./test-remote.sh vm1:9092 vm2:9092 vm3:9092
```

### 2️⃣ Environment Variables
```bash
export KAFKA_BROKERS="vm1:9092,vm2:9092,vm3:9092"
./run_stress_test.sh
```

### 3️⃣ Configuration File
```bash
cp .env.example .env
# Edit .env with your settings
source .env
./run_stress_test.sh
```

---

## Essential Environment Variables

| Variable | Example |
|----------|---------|
| `KAFKA_BROKERS` | `vm1:9092,vm2:9092,vm3:9092` |
| `NUM_PRODUCERS` | `20` |
| `MESSAGES_PER_PRODUCER` | `10000` |
| `MESSAGE_SIZE_BYTES` | `1024` |
| `NUM_CONSUMER_GROUPS` | `5` |
| `CONSUMERS_PER_GROUP` | `3` |

---

## Pre-Flight Checks

### Test Connectivity
```bash
nc -zv vm1.example.com 9092
```

### Verify Kafka Connection
```bash
python3 -c "
from confluent_kafka.admin import AdminClient
admin = AdminClient({'bootstrap.servers': 'vm1:9092,vm2:9092,vm3:9092'})
print(admin.list_topics(timeout=10).brokers)
"
```

---

## Common Scenarios

### Production Test
```bash
export KAFKA_BROKERS="prod-kafka1.company.com:9092,prod-kafka2.company.com:9092,prod-kafka3.company.com:9092"
./run_stress_test.sh
```

### High Throughput
```bash
export KAFKA_BROKERS="vm1:9092,vm2:9092,vm3:9092"
export NUM_PRODUCERS=20
export MESSAGES_PER_PRODUCER=50000
export MESSAGE_SIZE_BYTES=10240
./run_stress_test.sh
```

### Quick Smoke Test
```bash
export NUM_PRODUCERS=5
export MESSAGES_PER_PRODUCER=1000
./test-remote.sh kafka1:9092 kafka2:9092 kafka3:9092
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check firewall: `nc -zv host 9092` |
| DNS not resolving | Add to `/etc/hosts` or use IP |
| Advertised listener error | Check `KAFKA_ADVERTISED_LISTENERS` in docker-compose.yml |
| Timeout | Increase `TEST_DURATION_SECONDS=600` |

---

## Results

Results saved to:
- `test-results/STRESS_TEST_REPORT.md` - Main report
- `test-results/producer_results.json` - Producer metrics
- `test-results/consumer_results.json` - Consumer metrics

---

## More Info

📖 **Detailed Guide**: [REMOTE-TESTING-GUIDE.md](REMOTE-TESTING-GUIDE.md)  
📋 **Config Template**: [.env.example](.env.example)  
📚 **Full Docs**: [README.md](README.md)
