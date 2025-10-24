"""
Database models for HyperKit AI Agent production system.

This file defines the SQLAlchemy models for the production database schema.
These models will replace the current JSON file-based storage.
"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and management."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    tier = Column(String(50), default='free', nullable=False)  # free, paid, enterprise
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    deployments = relationship("Deployment", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Deployment(Base):
    """Deployment model for tracking contract deployments."""
    
    __tablename__ = "deployments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contract_address = Column(String(42), nullable=True, index=True)  # Ethereum address
    contract_name = Column(String(255), nullable=False)
    contract_code = Column(Text, nullable=False)
    network = Column(String(50), nullable=False)  # mainnet, goerli, sepolia, etc.
    status = Column(String(50), nullable=False)  # pending, compiling, deploying, deployed, failed
    gas_used = Column(BigInteger, nullable=True)
    gas_price = Column(BigInteger, nullable=True)
    transaction_hash = Column(String(66), nullable=True, index=True)
    block_number = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional metadata
    constructor_args = Column(JSON, nullable=True)
    compilation_errors = Column(Text, nullable=True)
    deployment_errors = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="deployments")
    audit_logs = relationship("AuditLog", back_populates="deployment")


class AuditLog(Base):
    """Audit log model for compliance and security tracking."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=True)
    action = Column(String(100), nullable=False)  # login, deploy, audit, etc.
    resource_type = Column(String(50), nullable=True)  # contract, user, system
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    deployment = relationship("Deployment", back_populates="audit_logs")


class Job(Base):
    """Job model for tracking async job processing."""
    
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=True)
    job_type = Column(String(50), nullable=False)  # compile, deploy, audit
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    deployment = relationship("Deployment")


class ContractTemplate(Base):
    """Contract template model for storing reusable contract templates."""
    
    __tablename__ = "contract_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_code = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # erc20, erc721, governance, etc.
    is_public = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")


class SecurityAudit(Base):
    """Security audit model for tracking contract security assessments."""
    
    __tablename__ = "security_audits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=False)
    audit_type = Column(String(50), nullable=False)  # automated, manual, external
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    findings = Column(JSON, nullable=True)  # Array of security findings
    risk_level = Column(String(20), nullable=True)  # low, medium, high, critical
    auditor = Column(String(255), nullable=True)  # Name of auditor or tool
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    deployment = relationship("Deployment")


class APIRateLimit(Base):
    """API rate limit model for tracking user API usage."""
    
    __tablename__ = "api_rate_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(255), nullable=False)
    requests_count = Column(Integer, default=0, nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
