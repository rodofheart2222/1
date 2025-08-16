"""
MT5 Communication Interface

This module provides utilities for communicating with MT5 Expert Advisors
through Global Variables and file-based fallback mechanisms.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SoldierReport:
    """Data structure for Soldier EA reports"""
    magic_number: int
    symbol: str
    strategy_tag: str
    current_profit: float
    open_positions: int
    trade_status: str
    sl_value: float
    tp_value: float
    trailing_active: bool
    module_status: Dict[str, str]  # {BB: active, RSI: signal, MA: trend}
    performance_metrics: Dict[str, float]  # {pf, ep, dd, zscore}
    last_trades: List[Dict[str, Any]]  # Last 10 trades
    coc_override: bool
    last_update: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SoldierReport':
        """Create SoldierReport from dictionary"""
        # Convert string datetime back to datetime object
        if isinstance(data.get('last_update'), str):
            data['last_update'] = datetime.fromisoformat(data['last_update'])
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert SoldierReport to dictionary"""
        data = asdict(self)
        # Convert datetime to string for JSON serialization
        if isinstance(data['last_update'], datetime):
            data['last_update'] = data['last_update'].isoformat()
        return data


class MT5GlobalVariables:
    """
    Utility class for reading and writing MT5 Global Variables.
    
    Since we can't directly access MT5 Global Variables from Python,
    this implementation uses a file-based approach where MT5 EAs
    write their Global Variables to files that Python can read.
    """
    
    def __init__(self, data_directory: str = "data/mt5_globals"):
        """
        Initialize MT5 Global Variables interface
        
        Args:
            data_directory: Directory where MT5 global variable files are stored
        """
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"MT5 Global Variables interface initialized with directory: {self.data_directory}")

    def read_global_variable(self, variable_name: str) -> Optional[str]:
        """
        Read a global variable value from file
        
        Args:
            variable_name: Name of the global variable
            
        Returns:
            Variable value as string, or None if not found
        """
        try:
            file_path = self.data_directory / f"{variable_name}.txt"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    logger.debug(f"Read global variable {variable_name}: {content[:100]}...")
                    return content
            else:
                logger.debug(f"Global variable file not found: {variable_name}")
                return None
        except Exception as e:
            logger.error(f"Error reading global variable {variable_name}: {e}")
            return None

    def write_global_variable(self, variable_name: str, value: str) -> bool:
        """
        Write a global variable value to file
        
        Args:
            variable_name: Name of the global variable
            value: Value to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.data_directory / f"{variable_name}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(value)
            logger.debug(f"Wrote global variable {variable_name}: {value[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Error writing global variable {variable_name}: {e}")
            return False

    def list_global_variables(self, prefix: str = "") -> List[str]:
        """
        List all global variables with optional prefix filter
        
        Args:
            prefix: Optional prefix to filter variables
            
        Returns:
            List of variable names
        """
        try:
            variables = []
            for file_path in self.data_directory.glob("*.txt"):
                var_name = file_path.stem
                if not prefix or var_name.startswith(prefix):
                    variables.append(var_name)
            logger.debug(f"Found {len(variables)} global variables with prefix '{prefix}'")
            return variables
        except Exception as e:
            logger.error(f"Error listing global variables: {e}")
            return []

    def delete_global_variable(self, variable_name: str) -> bool:
        """
        Delete a global variable file
        
        Args:
            variable_name: Name of the global variable to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.data_directory / f"{variable_name}.txt"
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted global variable: {variable_name}")
                return True
            else:
                logger.debug(f"Global variable not found for deletion: {variable_name}")
                return False
        except Exception as e:
            logger.error(f"Error deleting global variable {variable_name}: {e}")
            return False

    def get_variable_timestamp(self, variable_name: str) -> Optional[datetime]:
        """
        Get the last modification timestamp of a global variable file
        
        Args:
            variable_name: Name of the global variable
            
        Returns:
            Last modification datetime, or None if file doesn't exist
        """
        try:
            file_path = self.data_directory / f"{variable_name}.txt"
            if file_path.exists():
                timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                return timestamp
            return None
        except Exception as e:
            logger.error(f"Error getting timestamp for {variable_name}: {e}")
            return None


class MT5CommandWriter:
    """
    Utility class for writing commands to MT5 EAs through Global Variables
    """
    
    def __init__(self, global_vars: MT5GlobalVariables):
        """
        Initialize command writer
        
        Args:
            global_vars: MT5GlobalVariables instance
        """
        self.global_vars = global_vars
        logger.info("MT5 Command Writer initialized")

    def send_command(self, magic_number: int, command_type: str, parameters: Dict[str, Any] = None) -> bool:
        """
        Send a command to a specific EA
        
        Args:
            magic_number: EA magic number
            command_type: Type of command (pause, resume, adjust_risk, etc.)
            parameters: Optional command parameters
            
        Returns:
            True if command was written successfully
        """
        try:
            command_data = {
                'command_type': command_type,
                'parameters': parameters or {},
                'timestamp': datetime.now().isoformat(),
                'magic_number': magic_number
            }
            
            variable_name = f"COC_CMD_{magic_number}"
            command_json = json.dumps(command_data)
            
            success = self.global_vars.write_global_variable(variable_name, command_json)
            if success:
                logger.info(f"Sent command {command_type} to EA {magic_number}")
            else:
                logger.error(f"Failed to send command {command_type} to EA {magic_number}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending command to EA {magic_number}: {e}")
            return False

    def send_batch_command(self, magic_numbers: List[int], command_type: str, parameters: Dict[str, Any] = None) -> Dict[int, bool]:
        """
        Send the same command to multiple EAs
        
        Args:
            magic_numbers: List of EA magic numbers
            command_type: Type of command
            parameters: Optional command parameters
            
        Returns:
            Dictionary mapping magic_number to success status
        """
        results = {}
        for magic_number in magic_numbers:
            results[magic_number] = self.send_command(magic_number, command_type, parameters)
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Batch command {command_type}: {successful}/{len(magic_numbers)} successful")
        
        return results

    def clear_command(self, magic_number: int) -> bool:
        """
        Clear/delete a command for a specific EA
        
        Args:
            magic_number: EA magic number
            
        Returns:
            True if command was cleared successfully
        """
        variable_name = f"COC_CMD_{magic_number}"
        success = self.global_vars.delete_global_variable(variable_name)
        if success:
            logger.debug(f"Cleared command for EA {magic_number}")
        return success


class MT5DataParser:
    """
    Parser for converting MT5 Global Variable strings to structured data
    """
    
    def __init__(self, global_vars: MT5GlobalVariables):
        """
        Initialize data parser
        
        Args:
            global_vars: MT5GlobalVariables instance
        """
        self.global_vars = global_vars
        logger.info("MT5 Data Parser initialized")

    def parse_ea_report(self, magic_number: int) -> Optional[SoldierReport]:
        """
        Parse EA report data from Global Variables
        
        Args:
            magic_number: EA magic number
            
        Returns:
            SoldierReport object or None if parsing fails
        """
        try:
            variable_name = f"COC_EA_{magic_number}_DATA"
            raw_data = self.global_vars.read_global_variable(variable_name)
            
            if not raw_data:
                logger.debug(f"No data found for EA {magic_number}")
                return None
            
            # Parse JSON data
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON data for EA {magic_number}: {e}")
                return None
            
            # Validate required fields
            required_fields = [
                'magic_number', 'symbol', 'strategy_tag', 'current_profit',
                'open_positions', 'trade_status', 'sl_value', 'tp_value',
                'trailing_active', 'module_status', 'performance_metrics',
                'last_trades', 'coc_override', 'last_update'
            ]
            
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in EA {magic_number} data")
                    return None
            
            # Parse and validate data types
            parsed_data = self._validate_and_convert_data(data, magic_number)
            if not parsed_data:
                return None
            
            # Create SoldierReport object
            report = SoldierReport.from_dict(parsed_data)
            logger.debug(f"Successfully parsed EA {magic_number} report")
            return report
            
        except Exception as e:
            logger.error(f"Error parsing EA {magic_number} report: {e}")
            return None

    def _validate_and_convert_data(self, data: Dict[str, Any], magic_number: int) -> Optional[Dict[str, Any]]:
        """
        Validate and convert data types for EA report
        
        Args:
            data: Raw data dictionary
            magic_number: EA magic number for logging
            
        Returns:
            Validated and converted data dictionary or None if validation fails
        """
        try:
            validated_data = {}
            
            # Integer fields
            validated_data['magic_number'] = int(data['magic_number'])
            validated_data['open_positions'] = int(data['open_positions'])
            
            # String fields
            validated_data['symbol'] = str(data['symbol'])
            validated_data['strategy_tag'] = str(data['strategy_tag'])
            validated_data['trade_status'] = str(data['trade_status'])
            
            # Float fields
            validated_data['current_profit'] = float(data['current_profit'])
            validated_data['sl_value'] = float(data['sl_value'])
            validated_data['tp_value'] = float(data['tp_value'])
            
            # Boolean fields
            validated_data['trailing_active'] = bool(data['trailing_active'])
            validated_data['coc_override'] = bool(data['coc_override'])
            
            # JSON fields - module_status
            if isinstance(data['module_status'], str):
                validated_data['module_status'] = json.loads(data['module_status'])
            else:
                validated_data['module_status'] = data['module_status']
            
            # JSON fields - performance_metrics
            if isinstance(data['performance_metrics'], str):
                validated_data['performance_metrics'] = json.loads(data['performance_metrics'])
            else:
                validated_data['performance_metrics'] = data['performance_metrics']
            
            # JSON fields - last_trades
            if isinstance(data['last_trades'], str):
                validated_data['last_trades'] = json.loads(data['last_trades'])
            else:
                validated_data['last_trades'] = data['last_trades']
            
            # Datetime field
            if isinstance(data['last_update'], str):
                validated_data['last_update'] = datetime.fromisoformat(data['last_update'])
            else:
                validated_data['last_update'] = data['last_update']
            
            return validated_data
            
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.error(f"Data validation failed for EA {magic_number}: {e}")
            return None

    def parse_all_ea_reports(self) -> Dict[int, SoldierReport]:
        """
        Parse reports from all active EAs
        
        Returns:
            Dictionary mapping magic_number to SoldierReport
        """
        reports = {}
        
        # Find all EA data variables
        ea_variables = self.global_vars.list_global_variables("COC_EA_")
        
        # Extract magic numbers from variable names
        magic_numbers = set()
        for var_name in ea_variables:
            if "_DATA" in var_name:
                try:
                    # Extract magic number from "COC_EA_{magic}_DATA"
                    parts = var_name.split("_")
                    if len(parts) >= 3:
                        magic_number = int(parts[2])
                        magic_numbers.add(magic_number)
                except ValueError:
                    logger.warning(f"Invalid magic number in variable name: {var_name}")
                    continue
        
        # Parse each EA report
        for magic_number in magic_numbers:
            report = self.parse_ea_report(magic_number)
            if report:
                reports[magic_number] = report
        
        logger.info(f"Parsed {len(reports)} EA reports")
        return reports

    def validate_ea_data_format(self, data_string: str) -> bool:
        """
        Validate that EA data string is in correct format
        
        Args:
            data_string: Raw EA data string
            
        Returns:
            True if format is valid
        """
        try:
            data = json.loads(data_string)
            
            # Check required fields exist
            required_fields = [
                'magic_number', 'symbol', 'strategy_tag', 'current_profit',
                'open_positions', 'trade_status', 'sl_value', 'tp_value',
                'trailing_active', 'module_status', 'performance_metrics',
                'last_trades', 'coc_override', 'last_update'
            ]
            
            for field in required_fields:
                if field not in data:
                    return False
            
            # Basic type checking
            if not isinstance(data['magic_number'], int):
                return False
            if not isinstance(data['symbol'], str):
                return False
            if not isinstance(data['current_profit'], (int, float)):
                return False
            
            return True
            
        except (json.JSONDecodeError, TypeError, KeyError):
            return False

    def create_sample_ea_data(self, magic_number: int) -> str:
        """
        Create sample EA data for testing purposes
        
        Args:
            magic_number: EA magic number
            
        Returns:
            JSON string with sample EA data
        """
        sample_data = {
            "magic_number": magic_number,
            "symbol": "EURUSD",
            "strategy_tag": "Compression_v1",
            "current_profit": 125.50,
            "open_positions": 2,
            "trade_status": "active",
            "sl_value": 1.0850,
            "tp_value": 1.0950,
            "trailing_active": True,
            "module_status": {
                "BB": "active",
                "RSI": "signal",
                "MA": "trend",
                "Expansion": "inactive"
            },
            "performance_metrics": {
                "total_profit": 1250.75,
                "profit_factor": 1.45,
                "expected_payoff": 12.5,
                "drawdown": 8.2,
                "z_score": 2.1
            },
            "last_trades": [
                {
                    "type": "BUY",
                    "symbol": "EURUSD",
                    "volume": 1.0,
                    "price": 1.0875,
                    "profit": 25.50,
                    "timestamp": "2024-12-08T10:30:00"
                },
                {
                    "type": "SELL",
                    "symbol": "EURUSD",
                    "volume": 0.5,
                    "price": 1.0825,
                    "profit": -15.25,
                    "timestamp": "2024-12-08T09:15:00"
                }
            ],
            "coc_override": False,
            "last_update": datetime.now().isoformat()
        }
        
        return json.dumps(sample_data, indent=2)


class MT5HeartbeatMonitor:
    """
    Heartbeat monitoring system to detect disconnected EAs
    """
    
    def __init__(self, global_vars: MT5GlobalVariables, timeout_seconds: int = 90):
        """
        Initialize heartbeat monitor
        
        Args:
            global_vars: MT5GlobalVariables instance
            timeout_seconds: Seconds after which EA is considered disconnected
        """
        self.global_vars = global_vars
        self.timeout_seconds = timeout_seconds
        self.known_eas: Dict[int, datetime] = {}
        self.disconnected_eas: Dict[int, datetime] = {}
        logger.info(f"MT5 Heartbeat Monitor initialized with {timeout_seconds}s timeout")

    def register_ea(self, magic_number: int) -> None:
        """
        Register an EA for heartbeat monitoring
        
        Args:
            magic_number: EA magic number
        """
        self.known_eas[magic_number] = datetime.now()
        # Remove from disconnected list if it was there
        if magic_number in self.disconnected_eas:
            del self.disconnected_eas[magic_number]
        logger.debug(f"Registered EA {magic_number} for heartbeat monitoring")

    def update_heartbeat(self, magic_number: int, last_update: datetime) -> None:
        """
        Update heartbeat timestamp for an EA
        
        Args:
            magic_number: EA magic number
            last_update: Last update timestamp from EA
        """
        self.known_eas[magic_number] = last_update
        # Remove from disconnected list if it was there
        if magic_number in self.disconnected_eas:
            del self.disconnected_eas[magic_number]
            logger.info(f"EA {magic_number} reconnected")

    def check_heartbeats(self) -> List[int]:
        """
        Check all registered EAs for heartbeat timeouts
        
        Returns:
            List of magic numbers for disconnected EAs
        """
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.timeout_seconds)
        newly_disconnected = []
        
        for magic_number, last_heartbeat in self.known_eas.items():
            time_since_heartbeat = current_time - last_heartbeat
            
            if time_since_heartbeat > timeout_threshold:
                if magic_number not in self.disconnected_eas:
                    # Newly disconnected EA
                    self.disconnected_eas[magic_number] = current_time
                    newly_disconnected.append(magic_number)
                    logger.warning(f"EA {magic_number} disconnected (last seen: {last_heartbeat})")
        
        return newly_disconnected

    def get_disconnected_eas(self) -> Dict[int, datetime]:
        """
        Get all currently disconnected EAs
        
        Returns:
            Dictionary mapping magic_number to disconnection time
        """
        return self.disconnected_eas.copy()

    def get_connected_eas(self) -> Dict[int, datetime]:
        """
        Get all currently connected EAs
        
        Returns:
            Dictionary mapping magic_number to last heartbeat time
        """
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.timeout_seconds)
        connected_eas = {}
        
        for magic_number, last_heartbeat in self.known_eas.items():
            time_since_heartbeat = current_time - last_heartbeat
            if time_since_heartbeat <= timeout_threshold:
                connected_eas[magic_number] = last_heartbeat
        
        return connected_eas

    def get_ea_status(self, magic_number: int) -> str:
        """
        Get connection status for a specific EA
        
        Args:
            magic_number: EA magic number
            
        Returns:
            Status string: 'connected', 'disconnected', or 'unknown'
        """
        if magic_number not in self.known_eas:
            return 'unknown'
        
        current_time = datetime.now()
        last_heartbeat = self.known_eas[magic_number]
        time_since_heartbeat = current_time - last_heartbeat
        timeout_threshold = timedelta(seconds=self.timeout_seconds)
        
        if time_since_heartbeat <= timeout_threshold:
            return 'connected'
        else:
            return 'disconnected'

    def get_heartbeat_stats(self) -> Dict[str, Any]:
        """
        Get heartbeat monitoring statistics
        
        Returns:
            Dictionary with monitoring statistics
        """
        connected = self.get_connected_eas()
        disconnected = self.get_disconnected_eas()
        
        stats = {
            'total_eas': len(self.known_eas),
            'connected_count': len(connected),
            'disconnected_count': len(disconnected),
            'timeout_seconds': self.timeout_seconds,
            'connected_eas': list(connected.keys()),
            'disconnected_eas': list(disconnected.keys()),
            'last_check': datetime.now().isoformat()
        }
        
        return stats

    def remove_ea(self, magic_number: int) -> bool:
        """
        Remove an EA from monitoring (when EA is permanently stopped)
        
        Args:
            magic_number: EA magic number
            
        Returns:
            True if EA was removed, False if not found
        """
        removed = False
        
        if magic_number in self.known_eas:
            del self.known_eas[magic_number]
            removed = True
        
        if magic_number in self.disconnected_eas:
            del self.disconnected_eas[magic_number]
            removed = True
        
        if removed:
            logger.info(f"Removed EA {magic_number} from heartbeat monitoring")
        
        return removed

    def cleanup_old_disconnected(self, hours: int = 24) -> List[int]:
        """
        Remove EAs that have been disconnected for too long
        
        Args:
            hours: Hours after which to remove disconnected EAs
            
        Returns:
            List of removed EA magic numbers
        """
        current_time = datetime.now()
        cleanup_threshold = timedelta(hours=hours)
        removed_eas = []
        
        for magic_number, disconnect_time in list(self.disconnected_eas.items()):
            time_since_disconnect = current_time - disconnect_time
            if time_since_disconnect > cleanup_threshold:
                self.remove_ea(magic_number)
                removed_eas.append(magic_number)
        
        if removed_eas:
            logger.info(f"Cleaned up {len(removed_eas)} old disconnected EAs: {removed_eas}")
        
        return removed_eas


class MT5FileFallback:
    """
    File-based fallback communication mechanism for when Global Variables fail
    """
    
    def __init__(self, fallback_directory: str = "data/mt5_fallback"):
        """
        Initialize file-based fallback system
        
        Args:
            fallback_directory: Directory for fallback communication files
        """
        self.fallback_directory = Path(fallback_directory)
        self.fallback_directory.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.ea_data_dir = self.fallback_directory / "ea_data"
        self.commands_dir = self.fallback_directory / "commands"
        self.heartbeat_dir = self.fallback_directory / "heartbeat"
        
        for directory in [self.ea_data_dir, self.commands_dir, self.heartbeat_dir]:
            directory.mkdir(exist_ok=True)
        
        logger.info(f"MT5 File Fallback initialized with directory: {self.fallback_directory}")

    def write_ea_data(self, magic_number: int, data: Dict[str, Any]) -> bool:
        """
        Write EA data to fallback file
        
        Args:
            magic_number: EA magic number
            data: EA data dictionary
            
        Returns:
            True if successful
        """
        try:
            file_path = self.ea_data_dir / f"ea_{magic_number}.json"
            
            # Add timestamp
            data_with_timestamp = data.copy()
            data_with_timestamp['file_timestamp'] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_with_timestamp, f, indent=2)
            
            logger.debug(f"Wrote EA {magic_number} data to fallback file")
            return True
            
        except Exception as e:
            logger.error(f"Error writing EA {magic_number} fallback data: {e}")
            return False

    def read_ea_data(self, magic_number: int) -> Optional[Dict[str, Any]]:
        """
        Read EA data from fallback file
        
        Args:
            magic_number: EA magic number
            
        Returns:
            EA data dictionary or None if not found
        """
        try:
            file_path = self.ea_data_dir / f"ea_{magic_number}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Read EA {magic_number} data from fallback file")
            return data
            
        except Exception as e:
            logger.error(f"Error reading EA {magic_number} fallback data: {e}")
            return None

    def write_command(self, magic_number: int, command: Dict[str, Any]) -> bool:
        """
        Write command to fallback file
        
        Args:
            magic_number: EA magic number
            command: Command dictionary
            
        Returns:
            True if successful
        """
        try:
            file_path = self.commands_dir / f"cmd_{magic_number}.json"
            
            # Add timestamp
            command_with_timestamp = command.copy()
            command_with_timestamp['file_timestamp'] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(command_with_timestamp, f, indent=2)
            
            logger.debug(f"Wrote command for EA {magic_number} to fallback file")
            return True
            
        except Exception as e:
            logger.error(f"Error writing command for EA {magic_number}: {e}")
            return False

    def read_command(self, magic_number: int) -> Optional[Dict[str, Any]]:
        """
        Read command from fallback file
        
        Args:
            magic_number: EA magic number
            
        Returns:
            Command dictionary or None if not found
        """
        try:
            file_path = self.commands_dir / f"cmd_{magic_number}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                command = json.load(f)
            
            logger.debug(f"Read command for EA {magic_number} from fallback file")
            return command
            
        except Exception as e:
            logger.error(f"Error reading command for EA {magic_number}: {e}")
            return None

    def delete_command(self, magic_number: int) -> bool:
        """
        Delete command file after processing
        
        Args:
            magic_number: EA magic number
            
        Returns:
            True if successful
        """
        try:
            file_path = self.commands_dir / f"cmd_{magic_number}.json"
            
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted command file for EA {magic_number}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting command file for EA {magic_number}: {e}")
            return False

    def write_heartbeat(self, magic_number: int) -> bool:
        """
        Write heartbeat timestamp to fallback file
        
        Args:
            magic_number: EA magic number
            
        Returns:
            True if successful
        """
        try:
            file_path = self.heartbeat_dir / f"hb_{magic_number}.txt"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(datetime.now().isoformat())
            
            logger.debug(f"Wrote heartbeat for EA {magic_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing heartbeat for EA {magic_number}: {e}")
            return False

    def read_heartbeat(self, magic_number: int) -> Optional[datetime]:
        """
        Read heartbeat timestamp from fallback file
        
        Args:
            magic_number: EA magic number
            
        Returns:
            Heartbeat datetime or None if not found
        """
        try:
            file_path = self.heartbeat_dir / f"hb_{magic_number}.txt"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                timestamp_str = f.read().strip()
            
            heartbeat = datetime.fromisoformat(timestamp_str)
            logger.debug(f"Read heartbeat for EA {magic_number}: {heartbeat}")
            return heartbeat
            
        except Exception as e:
            logger.error(f"Error reading heartbeat for EA {magic_number}: {e}")
            return None

    def list_active_eas(self) -> List[int]:
        """
        List all EAs with recent data files
        
        Returns:
            List of magic numbers
        """
        try:
            magic_numbers = []
            
            for file_path in self.ea_data_dir.glob("ea_*.json"):
                try:
                    # Extract magic number from filename
                    filename = file_path.stem
                    magic_number = int(filename.split("_")[1])
                    magic_numbers.append(magic_number)
                except (ValueError, IndexError):
                    logger.warning(f"Invalid EA data filename: {file_path.name}")
                    continue
            
            logger.debug(f"Found {len(magic_numbers)} active EAs in fallback files")
            return magic_numbers
            
        except Exception as e:
            logger.error(f"Error listing active EAs: {e}")
            return []

    def cleanup_old_files(self, hours: int = 24) -> Dict[str, int]:
        """
        Clean up old fallback files
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            current_time = datetime.now()
            age_threshold = timedelta(hours=hours)
            
            cleanup_stats = {
                'ea_data_files': 0,
                'command_files': 0,
                'heartbeat_files': 0
            }
            
            # Clean up EA data files
            for file_path in self.ea_data_dir.glob("ea_*.json"):
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age > age_threshold:
                    file_path.unlink()
                    cleanup_stats['ea_data_files'] += 1
            
            # Clean up command files
            for file_path in self.commands_dir.glob("cmd_*.json"):
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age > age_threshold:
                    file_path.unlink()
                    cleanup_stats['command_files'] += 1
            
            # Clean up heartbeat files
            for file_path in self.heartbeat_dir.glob("hb_*.txt"):
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age > age_threshold:
                    file_path.unlink()
                    cleanup_stats['heartbeat_files'] += 1
            
            total_cleaned = sum(cleanup_stats.values())
            if total_cleaned > 0:
                logger.info(f"Cleaned up {total_cleaned} old fallback files: {cleanup_stats}")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during fallback file cleanup: {e}")
            return {'ea_data_files': 0, 'command_files': 0, 'heartbeat_files': 0}

    def get_file_stats(self) -> Dict[str, Any]:
        """
        Get statistics about fallback files
        
        Returns:
            Dictionary with file statistics
        """
        try:
            stats = {
                'ea_data_files': len(list(self.ea_data_dir.glob("ea_*.json"))),
                'command_files': len(list(self.commands_dir.glob("cmd_*.json"))),
                'heartbeat_files': len(list(self.heartbeat_dir.glob("hb_*.txt"))),
                'total_size_bytes': 0,
                'last_check': datetime.now().isoformat()
            }
            
            # Calculate total size
            for directory in [self.ea_data_dir, self.commands_dir, self.heartbeat_dir]:
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        stats['total_size_bytes'] += file_path.stat().st_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting file stats: {e}")
            return {
                'ea_data_files': 0,
                'command_files': 0,
                'heartbeat_files': 0,
                'total_size_bytes': 0,
                'last_check': datetime.now().isoformat()
            }


class MT5CommunicationInterface:
    """
    Main interface for MT5 communication combining all components
    """
    
    def __init__(self, 
                 global_vars_dir: str = "data/mt5_globals",
                 fallback_dir: str = "data/mt5_fallback",
                 heartbeat_timeout: int = 90):
        """
        Initialize MT5 communication interface
        
        Args:
            global_vars_dir: Directory for global variables
            fallback_dir: Directory for fallback files
            heartbeat_timeout: Heartbeat timeout in seconds
        """
        self.global_vars = MT5GlobalVariables(global_vars_dir)
        self.data_parser = MT5DataParser(self.global_vars)
        self.command_writer = MT5CommandWriter(self.global_vars)
        self.heartbeat_monitor = MT5HeartbeatMonitor(self.global_vars, heartbeat_timeout)
        self.file_fallback = MT5FileFallback(fallback_dir)
        
        self.use_fallback = False  # Flag to switch to fallback mode
        
        logger.info("MT5 Communication Interface initialized")

    def collect_ea_data(self) -> Dict[int, SoldierReport]:
        """
        Collect data from all active EAs
        
        Returns:
            Dictionary mapping magic_number to SoldierReport
        """
        try:
            if self.use_fallback:
                return self._collect_ea_data_fallback()
            else:
                return self._collect_ea_data_global_vars()
        except Exception as e:
            logger.error(f"Error collecting EA data: {e}")
            # Try fallback if global vars fail
            if not self.use_fallback:
                logger.info("Switching to fallback mode due to error")
                self.use_fallback = True
                return self._collect_ea_data_fallback()
            return {}

    def _collect_ea_data_global_vars(self) -> Dict[int, SoldierReport]:
        """Collect EA data using Global Variables"""
        reports = self.data_parser.parse_all_ea_reports()
        
        # Update heartbeat monitor
        for magic_number, report in reports.items():
            self.heartbeat_monitor.update_heartbeat(magic_number, report.last_update)
        
        return reports

    def _collect_ea_data_fallback(self) -> Dict[int, SoldierReport]:
        """Collect EA data using fallback files"""
        reports = {}
        active_eas = self.file_fallback.list_active_eas()
        
        for magic_number in active_eas:
            data = self.file_fallback.read_ea_data(magic_number)
            if data:
                try:
                    # Remove file_timestamp if present (added by fallback system)
                    if 'file_timestamp' in data:
                        del data['file_timestamp']
                    
                    # Convert to SoldierReport
                    report = SoldierReport.from_dict(data)
                    reports[magic_number] = report
                    
                    # Update heartbeat monitor
                    self.heartbeat_monitor.update_heartbeat(magic_number, report.last_update)
                except Exception as e:
                    logger.error(f"Error parsing fallback data for EA {magic_number}: {e}")
        
        return reports

    def send_command(self, magic_number: int, command_type: str, parameters: Dict[str, Any] = None) -> bool:
        """
        Send command to EA
        
        Args:
            magic_number: EA magic number
            command_type: Command type
            parameters: Command parameters
            
        Returns:
            True if successful
        """
        try:
            if self.use_fallback:
                command_data = {
                    'command_type': command_type,
                    'parameters': parameters or {},
                    'timestamp': datetime.now().isoformat(),
                    'magic_number': magic_number
                }
                return self.file_fallback.write_command(magic_number, command_data)
            else:
                success = self.command_writer.send_command(magic_number, command_type, parameters)
                if not success:
                    # Try fallback
                    logger.info(f"Command failed via global vars, trying fallback for EA {magic_number}")
                    command_data = {
                        'command_type': command_type,
                        'parameters': parameters or {},
                        'timestamp': datetime.now().isoformat(),
                        'magic_number': magic_number
                    }
                    return self.file_fallback.write_command(magic_number, command_data)
                return success
        except Exception as e:
            logger.error(f"Error sending command to EA {magic_number}: {e}")
            return False

    def send_batch_command(self, magic_numbers: List[int], command_type: str, parameters: Dict[str, Any] = None) -> Dict[int, bool]:
        """
        Send batch command to multiple EAs
        
        Args:
            magic_numbers: List of EA magic numbers
            command_type: Command type
            parameters: Command parameters
            
        Returns:
            Dictionary mapping magic_number to success status
        """
        results = {}
        for magic_number in magic_numbers:
            results[magic_number] = self.send_command(magic_number, command_type, parameters)
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Batch command {command_type}: {successful}/{len(magic_numbers)} successful")
        
        return results

    def check_ea_connections(self) -> Dict[str, List[int]]:
        """
        Check EA connection status
        
        Returns:
            Dictionary with connected and disconnected EA lists
        """
        newly_disconnected = self.heartbeat_monitor.check_heartbeats()
        
        if newly_disconnected:
            logger.warning(f"Detected {len(newly_disconnected)} newly disconnected EAs: {newly_disconnected}")
        
        return {
            'connected': list(self.heartbeat_monitor.get_connected_eas().keys()),
            'disconnected': list(self.heartbeat_monitor.get_disconnected_eas().keys()),
            'newly_disconnected': newly_disconnected
        }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status
        
        Returns:
            Dictionary with system status information
        """
        heartbeat_stats = self.heartbeat_monitor.get_heartbeat_stats()
        file_stats = self.file_fallback.get_file_stats()
        
        status = {
            'communication_mode': 'fallback' if self.use_fallback else 'global_variables',
            'heartbeat_stats': heartbeat_stats,
            'file_stats': file_stats,
            'system_time': datetime.now().isoformat()
        }
        
        return status

    def switch_to_fallback_mode(self) -> None:
        """Switch to fallback communication mode"""
        self.use_fallback = True
        logger.info("Switched to fallback communication mode")

    def switch_to_global_vars_mode(self) -> None:
        """Switch to global variables communication mode"""
        self.use_fallback = False
        logger.info("Switched to global variables communication mode")

    def cleanup_old_data(self, hours: int = 24) -> Dict[str, Any]:
        """
        Clean up old data files and disconnected EAs
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            Cleanup statistics
        """
        file_cleanup = self.file_fallback.cleanup_old_files(hours)
        removed_eas = self.heartbeat_monitor.cleanup_old_disconnected(hours)
        
        cleanup_stats = {
            'file_cleanup': file_cleanup,
            'removed_eas': removed_eas,
            'cleanup_time': datetime.now().isoformat()
        }
        
        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats

    def test_communication(self, magic_number: int) -> Dict[str, Any]:
        """
        Test communication with a specific EA
        
        Args:
            magic_number: EA magic number to test
            
        Returns:
            Test results dictionary
        """
        test_results = {
            'magic_number': magic_number,
            'global_vars_test': False,
            'fallback_test': False,
            'heartbeat_status': 'unknown',
            'test_time': datetime.now().isoformat()
        }
        
        # Test global variables
        try:
            sample_data = self.data_parser.create_sample_ea_data(magic_number)
            var_name = f"COC_EA_{magic_number}_TEST"
            if self.global_vars.write_global_variable(var_name, sample_data):
                read_data = self.global_vars.read_global_variable(var_name)
                if read_data == sample_data:
                    test_results['global_vars_test'] = True
                self.global_vars.delete_global_variable(var_name)
        except Exception as e:
            logger.error(f"Global vars test failed for EA {magic_number}: {e}")
        
        # Test fallback
        try:
            test_data = {'test': True, 'magic_number': magic_number}
            if self.file_fallback.write_ea_data(magic_number, test_data):
                read_data = self.file_fallback.read_ea_data(magic_number)
                if read_data and read_data.get('test') == True:
                    test_results['fallback_test'] = True
        except Exception as e:
            logger.error(f"Fallback test failed for EA {magic_number}: {e}")
        
        # Check heartbeat status
        test_results['heartbeat_status'] = self.heartbeat_monitor.get_ea_status(magic_number)
        
        return test_results