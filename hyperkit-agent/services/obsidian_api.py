"""
Obsidian API Integration Service
Provides integration with Obsidian vault for RAG and knowledge management
"""

import os
import json
import requests
import logging
import urllib3
from typing import Dict, List, Optional, Any
from datetime import datetime

# Disable SSL warnings for local development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ObsidianAPI:
    """
    Obsidian API client for vault integration
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:27124"):
        """
        Initialize Obsidian API client

        Args:
            api_key: Obsidian Local REST API key
            base_url: Obsidian API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Obsidian API

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(
                    url, headers=self.headers, timeout=10, verify=False
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=self.headers, json=data, timeout=10, verify=False
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=self.headers, json=data, timeout=10, verify=False
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=self.headers, timeout=10, verify=False
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Obsidian API request failed: {e}")
            raise Exception(f"Obsidian API request failed: {e}")

    def test_connection(self) -> bool:
        """
        Test connection to Obsidian API

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self._make_request("GET", "/")
            return (
                response.get("authenticated", False) and response.get("status") == "OK"
            )
        except Exception as e:
            logger.error(f"Obsidian API connection test failed: {e}")
            return False

    def get_vault_info(self) -> Dict[str, Any]:
        """
        Get vault information

        Returns:
            Vault information dictionary
        """
        return self._make_request("GET", "/")

    def get_all_notes(self) -> List[Dict[str, Any]]:
        """
        Get all notes from the vault

        Returns:
            List of note information dictionaries
        """
        try:
            all_notes = []
            # Get all folders
            response = self._make_request("GET", "/vault/")
            folders = response.get("files", [])

            for folder in folders:
                if folder.endswith("/"):
                    # Get files in this folder
                    folder_response = self._make_request("GET", f"/vault/{folder}")
                    files = folder_response.get("files", [])
                    for file in files:
                        if file.endswith(".md"):
                            all_notes.append(
                                {
                                    "path": f"{folder}{file}",
                                    "name": file,
                                    "folder": folder,
                                }
                            )

            return all_notes
        except Exception as e:
            logger.error(f"Failed to get all notes: {e}")
            return []

    def get_note_content(self, file_path: str) -> str:
        """
        Get content of a specific note

        Args:
            file_path: Path to the note file

        Returns:
            Note content as string
        """
        try:
            # URL encode the file path
            import urllib.parse

            encoded_path = urllib.parse.quote(file_path, safe="")
            url = f"{self.base_url}/vault/{encoded_path}"

            # Make direct request for text content
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to get note content for {file_path}: {e}")
            return ""

    def create_note(self, file_path: str, content: str) -> bool:
        """
        Create a new note

        Args:
            file_path: Path for the new note
            content: Note content

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {"path": file_path, "content": content}
            self._make_request("POST", "/vault/", data)
            logger.info(f"Created note: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create note {file_path}: {e}")
            return False

    def update_note(self, file_path: str, content: str) -> bool:
        """
        Update an existing note

        Args:
            file_path: Path to the note
            content: New content

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {"content": content}
            import urllib.parse

            encoded_path = urllib.parse.quote(file_path, safe="")
            self._make_request("PUT", f"/vault/{encoded_path}", data)
            logger.info(f"Updated note: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to update note {file_path}: {e}")
            return False

    def delete_note(self, file_path: str) -> bool:
        """
        Delete a note

        Args:
            file_path: Path to the note

        Returns:
            True if successful, False otherwise
        """
        try:
            import urllib.parse

            encoded_path = urllib.parse.quote(file_path, safe="")
            self._make_request("DELETE", f"/vault/{encoded_path}")
            logger.info(f"Deleted note: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete note {file_path}: {e}")
            return False

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search notes by content

        Args:
            query: Search query

        Returns:
            List of matching notes
        """
        try:
            data = {"query": query}
            response = self._make_request("POST", "/search/", data)
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Failed to search notes: {e}")
            return []

    def get_notes_by_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        Get all notes in a specific folder

        Args:
            folder_path: Path to the folder

        Returns:
            List of notes in the folder
        """
        try:
            all_notes = self.get_all_notes()
            folder_notes = [
                note
                for note in all_notes
                if note.get("path", "").startswith(folder_path)
            ]
            return folder_notes
        except Exception as e:
            logger.error(f"Failed to get notes from folder {folder_path}: {e}")
            return []

    def get_contract_templates(self) -> List[Dict[str, Any]]:
        """
        Get all contract templates from the Templates folder

        Returns:
            List of contract template notes
        """
        return self.get_notes_by_folder("Templates/")

    def get_audit_checklists(self) -> List[Dict[str, Any]]:
        """
        Get all audit checklists from the Audits folder

        Returns:
            List of audit checklist notes
        """
        return self.get_notes_by_folder("Audits/")

    def get_prompt_templates(self) -> List[Dict[str, Any]]:
        """
        Get all prompt templates from the Prompts folder

        Returns:
            List of prompt template notes
        """
        return self.get_notes_by_folder("Prompts/")

    def get_contract_patterns(self) -> List[Dict[str, Any]]:
        """
        Get all contract patterns from the Contracts folder

        Returns:
            List of contract pattern notes
        """
        return self.get_notes_by_folder("Contracts/")

    def create_contract_note(
        self,
        contract_name: str,
        contract_code: str,
        description: str = "",
        category: str = "Custom",
    ) -> bool:
        """
        Create a contract note in the Contracts folder

        Args:
            contract_name: Name of the contract
            contract_code: Solidity contract code
            description: Contract description
            category: Contract category

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# {contract_name}

**Category:** {category}  
**Created:** {timestamp}  
**Description:** {description}

## Contract Code

```solidity
{contract_code}
```

## Usage Notes

- Deploy using Hardhat or Remix
- Test thoroughly before mainnet deployment
- Consider security audit for production use
- Update gas estimates based on network conditions

## Security Considerations

- Review for common vulnerabilities
- Test with different input values
- Consider edge cases and error conditions
- Implement proper access controls

## Deployment Checklist

- [ ] Code review completed
- [ ] Unit tests written and passing
- [ ] Integration tests completed
- [ ] Security audit considered
- [ ] Gas optimization reviewed
- [ ] Documentation updated
"""

        file_path = f"Contracts/{contract_name}.md"
        return self.create_note(file_path, content)

    def create_audit_report(
        self, contract_name: str, audit_results: Dict[str, Any]
    ) -> bool:
        """
        Create an audit report in the Audits folder

        Args:
            contract_name: Name of the audited contract
            audit_results: Audit results dictionary

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Audit Report: {contract_name}

**Audit Date:** {timestamp}  
**Contract:** {contract_name}  
**Severity:** {audit_results.get('severity', 'Unknown')}

## Executive Summary

{audit_results.get('summary', 'No summary available')}

## Findings

### Critical Issues
{self._format_findings(audit_results.get('critical', []))}

### High Issues
{self._format_findings(audit_results.get('high', []))}

### Medium Issues
{self._format_findings(audit_results.get('medium', []))}

### Low Issues
{self._format_findings(audit_results.get('low', []))}

### Informational
{self._format_findings(audit_results.get('informational', []))}

## Recommendations

1. Address all critical and high severity issues immediately
2. Review medium severity issues for potential impact
3. Consider low severity issues for code quality improvements
4. Implement recommended security measures

## Next Steps

- [ ] Fix critical issues
- [ ] Address high severity issues
- [ ] Review and fix medium severity issues
- [ ] Consider low severity improvements
- [ ] Re-audit after fixes
- [ ] Deploy to testnet for validation
"""

        file_path = f"Audits/{contract_name}-Audit-{timestamp.replace(':', '-').replace(' ', '-')}.md"
        return self.create_note(file_path, content)

    def _format_findings(self, findings: List[Dict[str, Any]]) -> str:
        """
        Format findings for audit report

        Args:
            findings: List of findings

        Returns:
            Formatted findings string
        """
        if not findings:
            return "None"

        formatted = []
        for i, finding in enumerate(findings, 1):
            formatted.append(f"{i}. **{finding.get('title', 'Unknown Issue')}**")
            formatted.append(
                f"   - Description: {finding.get('description', 'No description')}"
            )
            if finding.get("recommendation"):
                formatted.append(
                    f"   - Recommendation: {finding.get('recommendation')}"
                )
            formatted.append("")

        return "\n".join(formatted)

    def get_knowledge_base_content(self) -> str:
        """
        Get all knowledge base content for RAG

        Returns:
            Combined content from all knowledge base files
        """
        try:
            all_notes = self.get_all_notes()
            content_parts = []

            for note in all_notes:
                file_path = note.get("path", "")
                if any(
                    folder in file_path
                    for folder in ["Contracts/", "Audits/", "Templates/", "Prompts/"]
                ):
                    content = self.get_note_content(file_path)
                    if content:
                        content_parts.append(f"=== {file_path} ===\n{content}\n")

            return "\n".join(content_parts)
        except Exception as e:
            logger.error(f"Failed to get knowledge base content: {e}")
            return ""

    def sync_vault(self) -> bool:
        """
        Sync vault with Git (if Obsidian Git plugin is enabled)

        Returns:
            True if successful, False otherwise
        """
        try:
            # This would require the Obsidian Git plugin to be configured
            # and the API endpoint to be available
            response = self._make_request("POST", "/git/sync")
            logger.info("Vault synced successfully")
            return True
        except Exception as e:
            logger.warning(f"Vault sync not available: {e}")
            return False
