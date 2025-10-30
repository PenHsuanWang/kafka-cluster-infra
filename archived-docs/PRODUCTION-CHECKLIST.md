# Production Deployment Checklist

## Pre-Deployment

### Infrastructure
- [ ] Verify minimum 24GB RAM available (8GB heap × 3 brokers)
- [ ] Verify minimum 100GB disk space per broker
- [ ] Ensure Docker 20.10+ and Docker Compose 2.0+ installed
- [ ] Verify network connectivity between all nodes
- [ ] Check firewall rules allow required ports

### Configuration Review
- [ ] Review and adjust heap size in `.env` (KAFKA_HEAP_SIZE)
- [ ] Update external host addresses for client access
- [ ] Review log retention settings (LOG_RETENTION_HOURS)
- [ ] Verify replication factor (default: 3)
- [ ] Verify min.insync.replicas (default: 2)

### Security (TODO for Production)
- [ ] Enable SSL/TLS encryption
  - Generate SSL certificates
  - Configure SSL listeners
  - Update client configs
- [ ] Enable SASL authentication
  - Choose SASL mechanism (SCRAM recommended)
  - Create user credentials
  - Configure ACLs
- [ ] Set up firewall rules
- [ ] Restrict ZooKeeper access
- [ ] Change default passwords
- [ ] Enable audit logging

## Deployment

### Initial Setup
- [ ] Clone repository to production server
- [ ] Review and customize `.env` file
- [ ] Validate docker-compose.yml: `make validate`
- [ ] Pull Docker images: `make pull`
- [ ] Start cluster: `make start`
- [ ] Wait for all services to be healthy (2-3 minutes)

### Validation
- [ ] Run health check: `make health`
- [ ] Verify all 3 ZooKeeper nodes are up
- [ ] Verify all 3 Kafka brokers are up
- [ ] Check Kafka UI is accessible: http://localhost:8080
- [ ] Verify no under-replicated partitions
- [ ] Check container resource usage

### Topic Configuration
- [ ] Create production topics: `make topics` or custom script
- [ ] Verify topic replication factor = 3
- [ ] Verify topic min.insync.replicas = 2
- [ ] Set appropriate partition counts per topic
- [ ] Configure retention policies per topic

### Performance Testing
- [ ] Run producer performance test: `make test`
- [ ] Verify target throughput achieved (~100 MB/s)
- [ ] Run consumer performance test
- [ ] Test with production-like message sizes
- [ ] Measure end-to-end latency

## Post-Deployment

### Monitoring Setup
- [ ] Set up Prometheus metrics collection
- [ ] Configure Grafana dashboards
- [ ] Set up log aggregation (ELK/Loki)
- [ ] Configure alerting rules
  - Under-replicated partitions > 0
  - ISR shrink rate > threshold
  - Disk usage > 80%
  - CPU usage > 70% sustained
  - Memory pressure
  - High request latency (p99 > 100ms)

### Key Metrics to Monitor
- [ ] Under-replicated partitions (should be 0)
- [ ] ISR shrink/expand rate
- [ ] Request latency (p50, p95, p99)
- [ ] Throughput (bytes in/out per second)
- [ ] Network utilization
- [ ] Disk utilization
- [ ] CPU usage
- [ ] Memory usage
- [ ] JVM GC pauses
- [ ] Active connections
- [ ] Consumer lag

### Backup and Recovery
- [ ] Document backup procedures
- [ ] Schedule regular ZooKeeper backups
- [ ] Test restore procedure
- [ ] Document disaster recovery plan
- [ ] Set up cross-datacenter replication (if needed)

### Documentation
- [ ] Document cluster architecture
- [ ] Document topic naming conventions
- [ ] Document access procedures
- [ ] Document escalation procedures
- [ ] Document common operations (adding brokers, etc.)
- [ ] Document troubleshooting steps

### Operational Procedures
- [ ] Test rolling restart procedure
- [ ] Test broker failover
- [ ] Test partition rebalancing
- [ ] Document maintenance windows
- [ ] Create runbooks for common issues

## Ongoing Operations

### Daily
- [ ] Check cluster health: `make health`
- [ ] Review alerting dashboard
- [ ] Check for under-replicated partitions
- [ ] Monitor disk usage trends

### Weekly
- [ ] Review performance metrics
- [ ] Check consumer lag
- [ ] Review error logs
- [ ] Verify backup completion

### Monthly
- [ ] Review capacity planning
- [ ] Test disaster recovery
- [ ] Update documentation
- [ ] Review and update ACLs
- [ ] Patch Docker images (if needed)

### Quarterly
- [ ] Performance tuning review
- [ ] Security audit
- [ ] Cost optimization review
- [ ] Architecture review

## Capacity Planning

### When to Scale
- [ ] Average CPU > 70% for 24 hours
- [ ] Disk usage > 80%
- [ ] Network utilization > 70%
- [ ] Request latency p99 > 100ms consistently
- [ ] Consumer lag consistently growing

### Scaling Options
- [ ] Vertical: Increase broker resources
- [ ] Horizontal: Add more brokers
- [ ] Add partitions to existing topics
- [ ] Implement topic archiving/compaction

## Security Hardening

### Network Security
- [ ] Use private network for broker communication
- [ ] Implement VPN for remote access
- [ ] Enable SSL for all connections
- [ ] Use dedicated subnets

### Access Control
- [ ] Implement least-privilege principle
- [ ] Use SASL for authentication
- [ ] Configure topic-level ACLs
- [ ] Rotate credentials regularly
- [ ] Audit access logs

### Data Protection
- [ ] Enable encryption at rest (if sensitive data)
- [ ] Enable encryption in transit (SSL/TLS)
- [ ] Implement data retention policies
- [ ] Configure audit logging

## Troubleshooting Reference

### Broker Not Starting
1. Check logs: `docker-compose logs kafka-X`
2. Verify ZooKeeper connectivity
3. Check memory/disk availability
4. Verify port availability

### Under-Replicated Partitions
1. Check broker health
2. Verify network connectivity
3. Check disk space
4. Review broker logs for errors

### High Latency
1. Check CPU/memory usage
2. Review GC logs
3. Check disk I/O
4. Verify network latency

### Consumer Lag
1. Check consumer group status
2. Verify consumer configuration
3. Check partition distribution
4. Consider adding consumers

## Success Criteria

- [ ] All brokers healthy for 24 hours
- [ ] Zero under-replicated partitions
- [ ] Request latency p99 < 100ms
- [ ] Target throughput achieved (100 MB/s)
- [ ] No critical alerts triggered
- [ ] Monitoring and alerting operational
- [ ] Documentation complete
- [ ] Team trained on operations

## Sign-Off

- [ ] Infrastructure team approval
- [ ] Security team approval
- [ ] Development team approval
- [ ] Operations team approval
- [ ] Management approval

---

**Date Deployed**: _______________

**Deployed By**: _______________

**Version**: _______________

**Environment**: _______________
