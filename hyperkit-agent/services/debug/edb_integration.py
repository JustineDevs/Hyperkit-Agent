"""
EDB Integration for HyperKit AI Agent
Provides interactive debugging capabilities for smart contracts
"""

import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class DebugSession:
    """Represents an active debugging session"""
    tx_hash: str
    rpc_url: str
    session_id: str
    status: str = "active"
    variables: Dict[str, Any] = None
    call_stack: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.call_stack is None:
            self.call_stack = []

class EDBIntegration:
    """Integration with EDB (Ethereum Debugger) for transaction debugging"""
    
    def __init__(self, edb_path: str = "edb"):
        self.edb_path = edb_path
        self.active_sessions: Dict[str, DebugSession] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "hyperkit_edb"
        self.temp_dir.mkdir(exist_ok=True)

    async def start_debug_session(self, tx_hash: str, rpc_url: str, contract_address: Optional[str] = None) -> DebugSession:
        """
        Start a new EDB debugging session
        
        Args:
            tx_hash: Transaction hash to debug
            rpc_url: RPC URL for the blockchain
            contract_address: Optional contract address for focused debugging
            
        Returns:
            DebugSession object
        """
        session_id = f"session_{tx_hash[:8]}"
        
        session = DebugSession(
            tx_hash=tx_hash,
            rpc_url=rpc_url,
            session_id=session_id
        )
        
        try:
            # Check if EDB is available
            if not await self._check_edb_availability():
                raise Exception("EDB is not installed or not available in PATH")
            
            # Start EDB session
            await self._launch_edb_session(session, contract_address)
            
            self.active_sessions[session_id] = session
            return session
            
        except Exception as e:
            session.status = "error"
            session.variables["error"] = str(e)
            return session

    async def step_through_transaction(self, session_id: str, steps: int = 1) -> Dict[str, Any]:
        """
        Step through transaction execution
        
        Args:
            session_id: Debug session ID
            steps: Number of steps to execute
            
        Returns:
            Dictionary with step results and variable states
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Execute EDB step command
            result = await self._execute_edb_command(
                session, 
                f"step {steps}"
            )
            
            # Parse EDB output
            parsed_result = self._parse_edb_output(result)
            
            # Update session state
            session.variables.update(parsed_result.get("variables", {}))
            session.call_stack = parsed_result.get("call_stack", [])
            
            return {
                "session_id": session_id,
                "step_count": steps,
                "variables": session.variables,
                "call_stack": session.call_stack,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "session_id": session_id,
                "error": str(e),
                "status": "error"
            }

    async def inspect_variable(self, session_id: str, variable_name: str) -> Dict[str, Any]:
        """
        Inspect specific variable value
        
        Args:
            session_id: Debug session ID
            variable_name: Name of variable to inspect
            
        Returns:
            Variable value and metadata
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Execute EDB inspect command
            result = await self._execute_edb_command(
                session,
                f"inspect {variable_name}"
            )
            
            # Parse variable information
            variable_info = self._parse_variable_info(result, variable_name)
            
            return {
                "session_id": session_id,
                "variable_name": variable_name,
                "value": variable_info.get("value"),
                "type": variable_info.get("type"),
                "memory_location": variable_info.get("memory_location"),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "session_id": session_id,
                "variable_name": variable_name,
                "error": str(e),
                "status": "error"
            }

    async def set_breakpoint(self, session_id: str, location: str) -> Dict[str, Any]:
        """
        Set breakpoint at specific location
        
        Args:
            session_id: Debug session ID
            location: Location to set breakpoint (e.g., "contract:function:line")
            
        Returns:
            Breakpoint information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Execute EDB breakpoint command
            result = await self._execute_edb_command(
                session,
                f"breakpoint {location}"
            )
            
            return {
                "session_id": session_id,
                "location": location,
                "breakpoint_id": result.get("breakpoint_id"),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "session_id": session_id,
                "location": location,
                "error": str(e),
                "status": "error"
            }

    async def get_call_stack(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get current call stack
        
        Args:
            session_id: Debug session ID
            
        Returns:
            List of call stack frames
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Execute EDB call stack command
            result = await self._execute_edb_command(session, "callstack")
            
            # Parse call stack
            call_stack = self._parse_call_stack(result)
            session.call_stack = call_stack
            
            return call_stack
            
        except Exception as e:
            return [{"error": str(e), "status": "error"}]

    async def end_debug_session(self, session_id: str) -> Dict[str, Any]:
        """
        End debugging session
        
        Args:
            session_id: Debug session ID
            
        Returns:
            Session summary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.status = "ended"
        
        # Clean up session resources
        await self._cleanup_session(session)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "tx_hash": session.tx_hash,
            "status": "ended",
            "total_steps": len(session.call_stack),
            "variables_inspected": len(session.variables)
        }

    async def _check_edb_availability(self) -> bool:
        """Check if EDB is available in the system"""
        try:
            result = subprocess.run(
                [self.edb_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    async def _launch_edb_session(self, session: DebugSession, contract_address: Optional[str] = None):
        """Launch EDB session for transaction debugging"""
        cmd = [
            self.edb_path,
            "--rpc-urls", session.rpc_url,
            "replay", session.tx_hash
        ]
        
        if contract_address:
            cmd.extend(["--contract", contract_address])
        
        # Start EDB process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.temp_dir)
        )
        
        # Store process reference
        session.variables["process"] = process

    async def _execute_edb_command(self, session: DebugSession, command: str) -> Dict[str, Any]:
        """Execute EDB command and return parsed result"""
        if "process" not in session.variables:
            raise Exception("EDB session not properly initialized")
        
        process = session.variables["process"]
        
        # Send command to EDB process
        process.stdin.write(f"{command}\n")
        process.stdin.flush()
        
        # Read output
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_lines.append(line.strip())
            
            # Check for command completion
            if "edb>" in line or "debug>" in line:
                break
        
        return self._parse_edb_output("\n".join(output_lines))

    def _parse_edb_output(self, output: str) -> Dict[str, Any]:
        """Parse EDB command output"""
        result = {
            "variables": {},
            "call_stack": [],
            "raw_output": output
        }
        
        lines = output.split("\n")
        
        for line in lines:
            # Parse variable assignments
            if "=" in line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    var_value = parts[1].strip()
                    result["variables"][var_name] = var_value
            
            # Parse call stack information
            if "->" in line or "at" in line:
                result["call_stack"].append({
                    "line": line.strip(),
                    "type": "call"
                })
        
        return result

    def _parse_variable_info(self, output: str, variable_name: str) -> Dict[str, Any]:
        """Parse variable inspection output"""
        lines = output.split("\n")
        
        for line in lines:
            if variable_name in line:
                # Extract value and type information
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        return {
                            "value": parts[1].strip(),
                            "type": "unknown",
                            "memory_location": "unknown"
                        }
        
        return {
            "value": "not_found",
            "type": "unknown",
            "memory_location": "unknown"
        }

    def _parse_call_stack(self, output: str) -> List[Dict[str, Any]]:
        """Parse call stack output"""
        call_stack = []
        lines = output.split("\n")
        
        for line in lines:
            if "->" in line or "at" in line:
                call_stack.append({
                    "frame": line.strip(),
                    "type": "call"
                })
        
        return call_stack

    async def _cleanup_session(self, session: DebugSession):
        """Clean up session resources"""
        if "process" in session.variables:
            process = session.variables["process"]
            if process.poll() is None:
                process.terminate()
                process.wait()

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        if session_id not in self.active_sessions:
            return {"status": "not_found"}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "tx_hash": session.tx_hash,
            "status": session.status,
            "variables_count": len(session.variables),
            "call_stack_depth": len(session.call_stack)
        }

    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active debugging sessions"""
        sessions = []
        
        for session_id, session in self.active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "tx_hash": session.tx_hash,
                "status": session.status,
                "variables_count": len(session.variables)
            })
        
        return sessions
