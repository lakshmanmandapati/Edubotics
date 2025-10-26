"""
BonicBot Controller Module

Provides both serial and WebSocket communication interfaces for controlling
BonicBot humanoid robots with comprehensive sequence and camera support.
"""

import asyncio
import websockets
import json
import logging
import serial
import time
import base64
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ ENUMS ============

class CommunicationType(Enum):
    """Communication interface types"""
    SERIAL = "serial"
    WEBSOCKET = "websocket"

class ServoID(Enum):
    """Servo identifier enumeration for BonicBot"""
    # Right hand servos
    RIGHT_GRIPPER = 'rightGripper'
    RIGHT_WRIST = 'rightWrist'
    RIGHT_ELBOW = 'rightElbow'
    RIGHT_SHOULDER_PITCH = 'rightSholderPitch'
    RIGHT_SHOULDER_YAW = 'rightSholderYaw'
    RIGHT_SHOULDER_ROLL = 'rightSholderRoll'
    
    # Left hand servos
    LEFT_GRIPPER = 'leftGripper'
    LEFT_WRIST = 'leftWrist'
    LEFT_ELBOW = 'leftElbow'
    LEFT_SHOULDER_PITCH = 'leftSholderPitch'
    LEFT_SHOULDER_YAW = 'leftSholderYaw'
    LEFT_SHOULDER_ROLL = 'leftSholderRoll'
    
    # Head servos
    HEAD_PAN = 'headPan'
    HEAD_TILT = 'headTilt'

class HeadModes(Enum):
    """Head expression modes"""
    NONE = 'None'
    NORMAL = 'Normal'
    HAPPY = 'Happy'
    SAD = 'Sad'
    ANGRY = 'Angry'
    SURPRISED = 'Surprised'
    CONFUSED = 'Confused'

class VideoStreamMode(Enum):
    """Video streaming modes"""
    NONE = 'None'
    ONE_WAY_FROM_ROBOT = 'OneWayFromRobot'
    ONE_WAY_TO_ROBOT = 'OneWayToRobot'
    TWO_WAY = 'TwoWay'

class MotorType(Enum):
    """Motor types for base movement"""
    GEAR_MOTOR = 'GearMotor'
    DDSM115 = 'DDSM115'

class SequenceAction(Enum):
    """Sequence control actions"""
    LIST = 'list'
    PLAY = 'play'
    STOP = 'stop'
    PAUSE = 'pause'
    RESUME = 'resume'
    STATUS = 'status'
    JUMPTO = 'jumpto'

class CameraAction(Enum):
    """Camera control actions"""
    START = 'start'
    STOP = 'stop'
    CAPTURE = 'capture'
    STATUS = 'status'
class RGBDisplayAction(Enum):
    """RGB Display control actions"""
    SET_TEXT = 'setText'
    SET_COLOR = 'setColor'
    SET_ANIMATION = 'setAnimation'
    SET_BRIGHTNESS = 'setBrightness'
    SET_SPEED = 'setSpeed'
    PLAY = 'play'
    PAUSE = 'pause'
    CLEAR = 'clear'
    SET_PIXEL = 'setPixel'

class AnimationMode(Enum):
    """LED matrix animation modes"""
    STATIC_TEXT = 0
    SCROLLING_TEXT = 1
    RAINBOW_WAVE = 2
    FIRE_EFFECT = 3
    PLASMA = 4
    MATRIX_RAIN = 5

# ============ CONSTANTS ============

class ServoConstants:
    """Servo angle limits and default values"""
    # Default values
    DEFAULT_ANGLE = 0.0
    DEFAULT_SPEED = 200.0
    DEFAULT_ACCELERATION = 20.0
    
    # Right hand limits
    RIGHT_GRIPPER_MIN, RIGHT_GRIPPER_MAX = -90.0, 90.0
    RIGHT_WRIST_MIN, RIGHT_WRIST_MAX = -90.0, 90.0
    RIGHT_ELBOW_MIN, RIGHT_ELBOW_MAX = -90.0, 0.0
    RIGHT_SHOULDER_PITCH_MIN, RIGHT_SHOULDER_PITCH_MAX = -45.0, 180.0
    RIGHT_SHOULDER_ROLL_MIN, RIGHT_SHOULDER_ROLL_MAX = -3.0, 144.0
    RIGHT_SHOULDER_YAW_MIN, RIGHT_SHOULDER_YAW_MAX = -90.0, 90.0
    
    # Left hand limits (same as right)
    LEFT_GRIPPER_MIN, LEFT_GRIPPER_MAX = -90.0, 90.0
    LEFT_WRIST_MIN, LEFT_WRIST_MAX = -90.0, 90.0
    LEFT_ELBOW_MIN, LEFT_ELBOW_MAX = -90.0, 0.0
    LEFT_SHOULDER_PITCH_MIN, LEFT_SHOULDER_PITCH_MAX = -45.0, 180.0
    LEFT_SHOULDER_ROLL_MIN, LEFT_SHOULDER_ROLL_MAX = -3.0, 144.0
    LEFT_SHOULDER_YAW_MIN, LEFT_SHOULDER_YAW_MAX = -90.0, 90.0
    
    # Head limits
    HEAD_PAN_MIN, HEAD_PAN_MAX = -90.0, 90.0
    HEAD_TILT_MIN, HEAD_TILT_MAX = -38.0, 45.0

# ============ DATA CLASSES ============

@dataclass
class ServoCommand:
    """Individual servo control command"""
    id: str
    angle: float
    speed: float = ServoConstants.DEFAULT_SPEED
    acc: float = ServoConstants.DEFAULT_ACCELERATION
    
    def validate_angle(self) -> bool:
        """Validate servo angle is within limits"""
        limits = self._get_servo_limits()
        if limits:
            min_angle, max_angle = limits
            return min_angle <= self.angle <= max_angle
        return True
    
    def _get_servo_limits(self) -> Optional[tuple]:
        """Get angle limits for this servo"""
        limits_map = {
            # Right hand
            ServoID.RIGHT_GRIPPER.value: (ServoConstants.RIGHT_GRIPPER_MIN, ServoConstants.RIGHT_GRIPPER_MAX),
            ServoID.RIGHT_WRIST.value: (ServoConstants.RIGHT_WRIST_MIN, ServoConstants.RIGHT_WRIST_MAX),
            ServoID.RIGHT_ELBOW.value: (ServoConstants.RIGHT_ELBOW_MIN, ServoConstants.RIGHT_ELBOW_MAX),
            ServoID.RIGHT_SHOULDER_PITCH.value: (ServoConstants.RIGHT_SHOULDER_PITCH_MIN, ServoConstants.RIGHT_SHOULDER_PITCH_MAX),
            ServoID.RIGHT_SHOULDER_YAW.value: (ServoConstants.RIGHT_SHOULDER_YAW_MIN, ServoConstants.RIGHT_SHOULDER_YAW_MAX),
            ServoID.RIGHT_SHOULDER_ROLL.value: (ServoConstants.RIGHT_SHOULDER_ROLL_MIN, ServoConstants.RIGHT_SHOULDER_ROLL_MAX),
            # Left hand
            ServoID.LEFT_GRIPPER.value: (ServoConstants.LEFT_GRIPPER_MIN, ServoConstants.LEFT_GRIPPER_MAX),
            ServoID.LEFT_WRIST.value: (ServoConstants.LEFT_WRIST_MIN, ServoConstants.LEFT_WRIST_MAX),
            ServoID.LEFT_ELBOW.value: (ServoConstants.LEFT_ELBOW_MIN, ServoConstants.LEFT_ELBOW_MAX),
            ServoID.LEFT_SHOULDER_PITCH.value: (ServoConstants.LEFT_SHOULDER_PITCH_MIN, ServoConstants.LEFT_SHOULDER_PITCH_MAX),
            ServoID.LEFT_SHOULDER_YAW.value: (ServoConstants.LEFT_SHOULDER_YAW_MIN, ServoConstants.LEFT_SHOULDER_YAW_MAX),
            ServoID.LEFT_SHOULDER_ROLL.value: (ServoConstants.LEFT_SHOULDER_ROLL_MIN, ServoConstants.LEFT_SHOULDER_ROLL_MAX),
            # Head
            ServoID.HEAD_PAN.value: (ServoConstants.HEAD_PAN_MIN, ServoConstants.HEAD_PAN_MAX),
            ServoID.HEAD_TILT.value: (ServoConstants.HEAD_TILT_MIN, ServoConstants.HEAD_TILT_MAX),
        }
        return limits_map.get(self.id)

@dataclass
class HeadCommand:
    """Head control command"""
    pan: float = 0.0
    tilt: float = 0.0
    mode: HeadModes = HeadModes.NONE
    speed: float = ServoConstants.DEFAULT_SPEED
    acceleration: float = ServoConstants.DEFAULT_ACCELERATION

@dataclass
class HandCommand:
    """Hand control command with all 6 servos"""
    shoulder_pitch: float = 0.0
    shoulder_yaw: float = 0.0
    shoulder_roll: float = 0.0
    elbow: float = 0.0
    wrist: float = 0.0
    gripper: float = 0.0
    speed: float = ServoConstants.DEFAULT_SPEED
    acceleration: float = ServoConstants.DEFAULT_ACCELERATION

@dataclass
class BaseCommand:
    """Base movement command"""
    left_motor_speed: float = 0.0
    right_motor_speed: float = 0.0
    motor_type: MotorType = MotorType.GEAR_MOTOR

@dataclass
class ServoReading:
    """Servo sensor reading"""
    id: str
    name: str
    feedback_angle: float
    feedback_speed: float
    load: float
    temperature: float
    has_error: bool

@dataclass
class BatteryReading:
    """Battery sensor reading"""
    voltage: float
    current: float
    soc: float  # State of charge
    temperature: float
    has_error: bool
    error_message: str

@dataclass
class MotorReading:
    """Motor sensor reading"""
    id: str
    feedback_speed: float
    feedback_position: float
    torque: float
    temperature: float
    mode: int
    has_error: bool

@dataclass
class SequenceInfo:
    """Sequence information"""
    id: str
    name: str
    description: str
    step_count: int
    duration: int
    is_loop: bool
    created_at: str
    component_usage: Dict[str, bool]

@dataclass
class SequenceStatus:
    """Current sequence playback status"""
    is_playing: bool
    is_paused: bool
    is_recording: bool
    current_sequence: Optional[str]
    current_step: int
    total_steps: int
    playback_progress: float
    available_sequence_count: int

@dataclass
class CameraStatus:
    """Camera status information"""
    is_streaming: bool
    is_initialized: bool
    connected_clients: int
    stream_url: Optional[str]

@dataclass
class CapturedImage:
    """Captured image data"""
    image_data: str  # Base64 encoded
    format: str
    timestamp: str

@dataclass
class RGBDisplayCommand:
    """RGB Display control command"""
    action: str
    payload: Dict[str, Any]

@dataclass
class RGBColor:
    """RGB color representation"""
    r: int = 0
    g: int = 0
    b: int = 0
    def __post_init__(self):
        for comp in [self.r, self.g, self.b]:
            if not 0 <= comp <= 255:
                raise ValueError(f"RGB values must be 0–255, got {comp}")

@dataclass
class PixelPosition:
    """LED matrix pixel position"""
    x: int
    y: int
    def __post_init__(self):
        if self.x < 0 or self.y < 0:
            raise ValueError(f"Pixel coordinates must be >= 0, got ({self.x},{self.y})")

class RGBDisplayConstants:
    """RGB LED Display constants"""
    MIN_BRIGHTNESS = 0
    MAX_BRIGHTNESS = 255
    MIN_SPEED = 1
    MAX_SPEED = 100
    DEFAULT_BRIGHTNESS = 128
    DEFAULT_SPEED = 50
    ANIMATION_MODES = [
        "Static Text",
        "Scrolling Text",
        "Rainbow Wave",
        "Fire Effect",
        "Plasma",
        "Matrix Rain"
    ]


# ============ BASE CONTROLLER INTERFACE ============

class BonicBotController:
    """
    Base controller class providing common interface for both
    serial and WebSocket communication with BonicBot.
    """
    
    def __init__(self, communication_type: CommunicationType):
        self.communication_type = communication_type
        self.connected = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ============ INTERFACE METHODS (to be implemented by subclasses) ============
    
    def connect(self) -> bool:
        """Connect to the robot"""
        raise NotImplementedError("Subclasses must implement connect()")
    
    def close(self):
        """Close connection to the robot"""
        raise NotImplementedError("Subclasses must implement close()")
    
    def is_connected(self) -> bool:
        """Check if connected to robot"""
        return self.connected
    
    # ============ COMMON CONTROL METHODS ============
    
    def control_servo(self, servo_id: Union[ServoID, str], angle: float, 
                     speed: float = None, acceleration: float = None) -> bool:
        """Control individual servo"""
        if isinstance(servo_id, ServoID):
            servo_id = servo_id.value
        
        cmd = ServoCommand(
            id=servo_id,
            angle=angle,
            speed=speed or ServoConstants.DEFAULT_SPEED,
            acc=acceleration or ServoConstants.DEFAULT_ACCELERATION
        )
        
        if not cmd.validate_angle():
            logger.error(f"Servo {servo_id} angle {angle} is out of bounds")
            return False
        
        return self._send_servo_command(cmd)
    
    def _send_servo_command(self, cmd: ServoCommand) -> bool:
        """Send servo command (implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _send_servo_command()")
    
    # ============ CONVENIENCE METHODS ============
    
    def control_head(self, pan_angle: float = None, tilt_angle: float = None, 
                    mode: HeadModes = None, speed: float = None) -> bool:
        """Control robot head"""
        if pan_angle is not None:
            self.control_servo(ServoID.HEAD_PAN, pan_angle, speed)
        if tilt_angle is not None:
            self.control_servo(ServoID.HEAD_TILT, tilt_angle, speed)
        if mode is not None:
            return self._set_head_mode(mode)
        return True
    
    def control_right_hand(self, gripper: float = None, wrist: float = None,
                          elbow: float = None, shoulder_pitch: float = None,
                          shoulder_yaw: float = None, shoulder_roll: float = None,
                          speed: float = None) -> bool:
        """Control right hand servos"""
        result = True
        if gripper is not None:
            result &= self.control_servo(ServoID.RIGHT_GRIPPER, gripper, speed)
        if wrist is not None:
            result &= self.control_servo(ServoID.RIGHT_WRIST, wrist, speed)
        if elbow is not None:
            result &= self.control_servo(ServoID.RIGHT_ELBOW, elbow, speed)
        if shoulder_pitch is not None:
            result &= self.control_servo(ServoID.RIGHT_SHOULDER_PITCH, shoulder_pitch, speed)
        if shoulder_yaw is not None:
            result &= self.control_servo(ServoID.RIGHT_SHOULDER_YAW, shoulder_yaw, speed)
        if shoulder_roll is not None:
            result &= self.control_servo(ServoID.RIGHT_SHOULDER_ROLL, shoulder_roll, speed)
        return result
    
    def control_left_hand(self, gripper: float = None, wrist: float = None,
                         elbow: float = None, shoulder_pitch: float = None,
                         shoulder_yaw: float = None, shoulder_roll: float = None,
                         speed: float = None) -> bool:
        """Control left hand servos"""
        result = True
        if gripper is not None:
            result &= self.control_servo(ServoID.LEFT_GRIPPER, gripper, speed)
        if wrist is not None:
            result &= self.control_servo(ServoID.LEFT_WRIST, wrist, speed)
        if elbow is not None:
            result &= self.control_servo(ServoID.LEFT_ELBOW, elbow, speed)
        if shoulder_pitch is not None:
            result &= self.control_servo(ServoID.LEFT_SHOULDER_PITCH, shoulder_pitch, speed)
        if shoulder_yaw is not None:
            result &= self.control_servo(ServoID.LEFT_SHOULDER_YAW, shoulder_yaw, speed)
        if shoulder_roll is not None:
            result &= self.control_servo(ServoID.LEFT_SHOULDER_ROLL, shoulder_roll, speed)
        return result
    
    def move_forward(self, speed: float = 100.0, duration: float = None):
        """Move robot forward"""
        return self._move_base(speed, speed, duration)
    
    def move_backward(self, speed: float = 100.0, duration: float = None):
        """Move robot backward"""
        return self._move_base(-speed, -speed, duration)
    
    def turn_left(self, speed: float = 100.0, duration: float = None):
        """Turn robot left"""
        return self._move_base(-speed, speed, duration)
    
    def turn_right(self, speed: float = 100.0, duration: float = None):
        """Turn robot right"""
        return self._move_base(speed, -speed, duration)
    
    def stop_movement(self):
        """Stop all robot movement"""
        return self._move_base(0, 0)
    
    # ============ ABSTRACT METHODS ============
    
    def _set_head_mode(self, mode: HeadModes) -> bool:
        """Set head expression mode (implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _set_head_mode()")
    
    def _move_base(self, left_speed: float, right_speed: float, duration: float = None) -> bool:
        """Move robot base (implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _move_base()")
        
    def _send_rgb_display_command(self, command: RGBDisplayCommand) -> bool:
        """Send RGB display command (implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _send_rgb_display_command()")


# ============ SERIAL CONTROLLER IMPLEMENTATION ============

class SerialBonicBotController(BonicBotController):
    """
    Serial communication implementation for BonicBot control.
    Preserves all existing serial control functionality.
    """
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        super().__init__(CommunicationType.SERIAL)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
    
    def connect(self) -> bool:
        """Connect to robot via serial"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.connected = True
            logger.info(f"Connected to robot on {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def close(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.connected = False
            logger.info("Serial connection closed")
    
    def _send_servo_command(self, cmd: ServoCommand) -> bool:
        """Send servo command via serial"""
        if not self.connected or not self.serial_connection:
            logger.error("Not connected to robot")
            return False
        
        try:
            # Format command for serial protocol
            command_str = f"SERVO:{cmd.id}:{cmd.angle}:{cmd.speed}:{cmd.acc}\n"
            self.serial_connection.write(command_str.encode())
            return True
        except Exception as e:
            logger.error(f"Failed to send servo command: {e}")
            return False
    
    def _set_head_mode(self, mode: HeadModes) -> bool:
        """Set head expression mode via serial"""
        if not self.connected or not self.serial_connection:
            logger.error("Not connected to robot")
            return False
        
        try:
            command_str = f"HEAD_MODE:{mode.value}\n"
            self.serial_connection.write(command_str.encode())
            return True
        except Exception as e:
            logger.error(f"Failed to set head mode: {e}")
            return False
    
    def _move_base(self, left_speed: float, right_speed: float, duration: float = None) -> bool:
        """Move robot base via serial"""
        if not self.connected or not self.serial_connection:
            logger.error("Not connected to robot")
            return False
        
        try:
            command_str = f"BASE:{left_speed}:{right_speed}\n"
            self.serial_connection.write(command_str.encode())
            
            if duration:
                time.sleep(duration)
                # Stop after duration
                stop_command = "BASE:0:0\n"
                self.serial_connection.write(stop_command.encode())
            
            return True
        except Exception as e:
            logger.error(f"Failed to move base: {e}")
            return False
    
    def read_sensor_data(self) -> Optional[str]:
        """Read sensor data from serial connection"""
        if not self.connected or not self.serial_connection:
            return None
        
        try:
            if self.serial_connection.in_waiting > 0:
                return self.serial_connection.readline().decode().strip()
        except Exception as e:
            logger.error(f"Error reading sensor data: {e}")
        
        return None
    
    # Serial doesn't support sequence/camera operations
    def speak(self, text: str) -> bool:
        """Speak text (not supported in serial mode)"""
        logger.warning("Speak function not supported in serial mode")
        return False
    
    def get_sequences(self) -> List[SequenceInfo]:
        """Get sequences (not supported in serial mode)"""
        logger.warning("Sequence operations not supported in serial mode")
        return []

# ============ WEBSOCKET CONTROLLER IMPLEMENTATION ============

class WebSocketBonicBotController(BonicBotController):
    """
    WebSocket communication implementation for BonicBot control.
    Provides enhanced sensor monitoring, sequence control, and camera operations.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        super().__init__(CommunicationType.WEBSOCKET)
        self.host = host
        self.port = port
        self.websocket = None
        self.client_id = None
        self.message_handler_task = None
        self.robot_status = {}
        self._stop_event = threading.Event()
        self._loop = None
        self._thread = None
        
        # Enhanced sensor data storage
        self.latest_sensor_data = {
            'battery': None, 'left_hand': None, 'right_hand': None,
            'head': None, 'base': None, 'distance': None, 'sequence': None, 'camera': None
        }
        self.sensor_history = {}
        self.sensor_listeners = {}
        self.data_callbacks = {}
        self.error_callbacks = {}
        
        # Sequence and camera status
        self.sequence_status = SequenceStatus(
            is_playing=False, is_paused=False, is_recording=False,
            current_sequence=None, current_step=0, total_steps=0,
            playback_progress=0.0, available_sequence_count=0
        )
        self.camera_status = CameraStatus(
            is_streaming=False, is_initialized=False,
            connected_clients=0, stream_url=None
        )
    
    def connect(self) -> bool:
        """Connect to robot via WebSocket"""
        try:
            # Start event loop in separate thread
            self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self._thread.start()
            
            # Wait for connection
            timeout = 10  # seconds
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def _run_event_loop(self):
        """Run event loop in separate thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._async_connect())
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            self._loop.close()
    
    async def _async_connect(self) -> bool:
        """Async connect to WebSocket server"""
        try:
            uri = f"ws://{self.host}:{self.port}"
            logger.info(f"Connecting to robot at {uri}")
            
            self.websocket = await websockets.connect(uri)
            self.connected = True
            
            # Start message handler
            self.message_handler_task = asyncio.create_task(self._handle_messages())
            
            logger.info("Connected to robot WebSocket server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def close(self):
        """Close WebSocket connection"""
        if self.connected:
            self._stop_event.set()
            
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._async_close(), self._loop)
            
            # Wait for thread to finish
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
    
    async def _async_close(self):
        """Async close WebSocket connection"""
        if self.websocket and self.connected:
            self.connected = False
            
            if self.message_handler_task:
                self.message_handler_task.cancel()
            
            await self.websocket.close()
            
            # Stop event loop
            if self._loop:
                self._loop.stop()
            
            logger.info("Disconnected from robot WebSocket server")
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._process_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message with enhanced data storage"""
        message_type = data.get('type')
        
        if message_type == 'welcome':
            self.client_id = data.get('clientId')
            self.robot_status = data.get('robotStatus', {})
            self._update_status_from_robot_data(self.robot_status)
            logger.info(f"Welcome message received. Client ID: {self.client_id}")
            
        elif message_type == 'response':
            success = data.get('success', False)
            command_type = data.get('commandType')
            data_type = data.get('dataType')
            result = data.get('result')
            
            if success:
                logger.debug(f"Command successful: {command_type}/{data_type}")
                if result:
                    self._store_sensor_data(data_type, result)
            else:
                error_msg = data.get('error', 'Unknown error')
                logger.error(f"Command failed: {command_type}/{data_type} - {error_msg}")
                
        elif message_type == 'continuousData':
            data_type = data.get('dataType')
            sensor_data = data.get('data')
            self._store_sensor_data(data_type, sensor_data)
            
        elif message_type == 'robotUpdate':
            self.robot_status = data.get('data', {})
            self._update_status_from_robot_data(self.robot_status)
            
        elif message_type == 'sequenceUpdate':
            sequence_data = data.get('data', {})
            self._update_sequence_status(sequence_data)
            
        elif message_type == 'error':
            error_msg = data.get('error')
            logger.error(f"Server error: {error_msg}")
    
    def _update_status_from_robot_data(self, robot_data: Dict[str, Any]):
        """Update local status from robot status data"""
        # Update sequence status
        sequence_status = robot_data.get('sequenceStatus', {})
        if sequence_status:
            self._update_sequence_status(sequence_status)
        
        # Update camera status
        camera_status = robot_data.get('cameraStatus', {})
        if camera_status:
            self.camera_status = CameraStatus(
                is_streaming=camera_status.get('isStreaming', False),
                is_initialized=camera_status.get('isInitialized', False),
                connected_clients=camera_status.get('connectedClients', 0),
                stream_url=camera_status.get('streamUrl')
            )
    
    def _update_sequence_status(self, sequence_data: Dict[str, Any]):
        """Update sequence status from incoming data"""
        self.sequence_status = SequenceStatus(
            is_playing=sequence_data.get('isPlaying', False),
            is_paused=sequence_data.get('isPaused', False),
            is_recording=sequence_data.get('isRecording', False),
            current_sequence=sequence_data.get('currentSequence'),
            current_step=sequence_data.get('currentStep', 0),
            total_steps=sequence_data.get('totalSteps', 0),
            playback_progress=sequence_data.get('playbackProgress', 0.0),
            available_sequence_count=sequence_data.get('availableSequenceCount', 0)
        )
    
    def _store_sensor_data(self, data_type: str, sensor_data: Dict[str, Any]):
        """Store sensor data and trigger listeners"""
        if not sensor_data:
            return
        
        storage_key = self._get_storage_key(data_type)
        if storage_key:
            # Store latest data
            self.latest_sensor_data[storage_key] = {
                'data': sensor_data,
                'timestamp': datetime.now(),
                'data_type': data_type
            }
            
            # Store in history (keep last 100 readings)
            if storage_key not in self.sensor_history:
                self.sensor_history[storage_key] = []
            
            self.sensor_history[storage_key].append({
                'data': sensor_data,
                'timestamp': datetime.now()
            })
            
            if len(self.sensor_history[storage_key]) > 100:
                self.sensor_history[storage_key] = self.sensor_history[storage_key][-100:]
            
            # Trigger listeners
            self._trigger_listeners(storage_key, sensor_data)
    
    def _get_storage_key(self, data_type: str) -> Optional[str]:
        """Map WebSocket data types to storage keys"""
        mapping = {
            'RobotDataType.battery': 'battery',
            'RobotDataType.leftHand': 'left_hand',
            'RobotDataType.rightHand': 'right_hand',
            'RobotDataType.head': 'head',
            'RobotDataType.base': 'base',
            'RobotDataType.distance': 'distance',
            'battery': 'battery',
            'lefthand': 'left_hand',
            'righthand': 'right_hand',
            'head': 'head',
            'base': 'base',
            'distance': 'distance',
            'sequence': 'sequence',
            'camera': 'camera'
        }
        return mapping.get(data_type)
    
    def _trigger_listeners(self, storage_key: str, sensor_data: Dict[str, Any]):
        """Trigger registered listeners for sensor data"""
        if storage_key in self.sensor_listeners:
            for listener_id, listener_config in self.sensor_listeners[storage_key].items():
                try:
                    callback = listener_config['callback']
                    data_filter = listener_config.get('filter')
                    
                    if data_filter and callable(data_filter):
                        if not data_filter(sensor_data):
                            continue
                    
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(sensor_data))
                    else:
                        callback(sensor_data)
                except Exception as e:
                    logger.error(f"Error in sensor listener {listener_id}: {e}")
    
    def _send_command_sync(self, command_type: str, data_type: str, 
                          payload: Dict[str, Any] = None, interval: int = 0) -> bool:
        """Send command synchronously"""
        if not self.connected or not self._loop:
            logger.error("Not connected to robot")
            return False
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._send_command(command_type, data_type, payload, interval),
                self._loop
            )
            return future.result(timeout=5)
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    async def _send_command(self, command_type: str, data_type: str, 
                           payload: Dict[str, Any] = None, interval: int = 0) -> bool:
        """Send command to the robot"""
        if not self.connected or not self.websocket:
            logger.error("Not connected to robot")
            return False
        
        message = {
            'commandType': command_type,
            'dataType': data_type,
            'payload': payload or {},
            'interval': interval
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def _send_servo_command(self, cmd: ServoCommand) -> bool:
        """Send servo command via WebSocket"""
        payload = asdict(cmd)
        return self._send_command_sync('command', 'servo', payload)
    
    def _set_head_mode(self, mode: HeadModes) -> bool:
        """Set head expression mode via WebSocket"""
        payload = {'mode': mode.value}
        return self._send_command_sync('command', 'head', payload)
    
    def _move_base(self, left_speed: float, right_speed: float, duration: float = None) -> bool:
        """Move robot base via WebSocket"""
        payload = {
            'leftMotor': {'currentSpeed': left_speed, 'type': MotorType.GEAR_MOTOR.value},
            'rightMotor': {'currentSpeed': right_speed, 'type': MotorType.GEAR_MOTOR.value}
        }
        result = self._send_command_sync('command', 'base', payload)
        
        if duration and result:
            time.sleep(duration)
            # Stop after duration
            stop_payload = {
                'leftMotor': {'currentSpeed': 0, 'type': MotorType.GEAR_MOTOR.value},
                'rightMotor': {'currentSpeed': 0, 'type': MotorType.GEAR_MOTOR.value}
            }
            self._send_command_sync('command', 'base', stop_payload)
        
        return result
        # ============ RGB DISPLAY OVER WEBSOCKET ============

    def _send_rgb_payload(self, payload: Dict[str, Any]) -> bool:
        """Send RGB display command; payload MUST contain 'action'"""
        # Note the camelCase dataType to match server expectations
        return self._send_command_sync('command', 'rgbDisplay', payload)

    def get_animation_modes(self) -> List[str]:
        """Return available animation mode names"""
        return RGBDisplayConstants.ANIMATION_MODES.copy()

    def set_display_text(self, text: str) -> bool:
        return self._send_rgb_payload({"action": "setText", "text": text})

    def set_display_color(self, r: int, g: int, b: int) -> bool:
        # Clamp to 0-255 to avoid server-side validation errors
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        return self._send_rgb_payload({"action": "setColor", "r": r, "g": g, "b": b})

    def set_display_animation(self, mode: Union[int, 'AnimationMode']) -> bool:
        mode_value = mode.value if isinstance(mode, AnimationMode) else int(mode)
        if not 0 <= mode_value < len(RGBDisplayConstants.ANIMATION_MODES):
            logger.error(f"Invalid animation mode: {mode_value}")
            return False
        return self._send_rgb_payload({"action": "setAnimation", "mode": mode_value})

    def set_display_brightness(self, brightness: int) -> bool:
        brightness = int(brightness)
        if not RGBDisplayConstants.MIN_BRIGHTNESS <= brightness <= RGBDisplayConstants.MAX_BRIGHTNESS:
            logger.error(f"Brightness must be between {RGBDisplayConstants.MIN_BRIGHTNESS}-{RGBDisplayConstants.MAX_BRIGHTNESS}")
            return False
        return self._send_rgb_payload({"action": "setBrightness", "value": brightness})

    def set_display_speed(self, speed: int) -> bool:
        speed = int(speed)
        if not RGBDisplayConstants.MIN_SPEED <= speed <= RGBDisplayConstants.MAX_SPEED:
            logger.error(f"Speed must be between {RGBDisplayConstants.MIN_SPEED}-{RGBDisplayConstants.MAX_SPEED}")
            return False
        return self._send_rgb_payload({"action": "setSpeed", "value": speed})

    def play_display_animation(self) -> bool:
        return self._send_rgb_payload({"action": "play"})

    def pause_display_animation(self) -> bool:
        return self._send_rgb_payload({"action": "pause"})

    def clear_display_matrix(self) -> bool:
        return self._send_rgb_payload({"action": "clear"})

    def set_display_pixel(self, x: int, y: int, r: int, g: int, b: int) -> bool:
        if x < 0 or y < 0:
            logger.error(f"Pixel coordinates must be non-negative, got: ({x}, {y})")
            return False
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        return self._send_rgb_payload({
            "action": "setPixel",
            "x": int(x), "y": int(y),
            "r": r, "g": g, "b": b
        })

    # Convenience helpers

    def display_text(self, text: str, color: tuple = None, animation_mode: Union[int, 'AnimationMode', None] = None) -> bool:
        ok = True
        if color:
            ok &= self.set_display_color(*color)
        if animation_mode is not None:
            ok &= self.set_display_animation(animation_mode)
        ok &= self.set_display_text(text)
        ok &= self.play_display_animation()
        return ok

    def create_rainbow_effect(self, speed: int = 50) -> bool:
        ok = self.set_display_animation(AnimationMode.RAINBOW_WAVE)
        ok &= self.set_display_speed(speed)
        ok &= self.play_display_animation()
        return ok

    # ============ ENHANCED SENSOR MONITORING METHODS ============
    
    def register_sensor_listener(self, sensor_type: str, listener_id: str, 
                                callback: Callable, data_filter: Callable = None) -> bool:
        """Register a listener for specific sensor data"""
        if sensor_type not in self.latest_sensor_data:
            logger.error(f"Invalid sensor type: {sensor_type}")
            return False
        
        if sensor_type not in self.sensor_listeners:
            self.sensor_listeners[sensor_type] = {}
        
        self.sensor_listeners[sensor_type][listener_id] = {
            'callback': callback,
            'filter': data_filter,
            'registered_at': datetime.now()
        }
        
        logger.info(f"Registered listener {listener_id} for {sensor_type}")
        return True
    
    def get_latest_sensor_data(self, sensor_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest sensor data for a specific sensor type"""
        return self.latest_sensor_data.get(sensor_type)
    
    def get_battery_status(self) -> Optional[BatteryReading]:
        """Get parsed battery status"""
        data = self.get_latest_sensor_data('battery')
        if data and data['data']:
            battery_data = data['data']
            return BatteryReading(
                voltage=battery_data.get('voltage', 0),
                current=battery_data.get('current', 0),
                soc=battery_data.get('soc', 0),
                temperature=battery_data.get('temperature', 0),
                has_error=battery_data.get('hasError', False),
                error_message=battery_data.get('errorMessage', '')
            )
        return None
    
    def get_distance_reading(self) -> Optional[float]:
        """Get latest distance sensor reading in mm"""
        data = self.get_latest_sensor_data('distance')
        if data and data['data']:
            return data['data'].get('distance')
        return None
    
    def start_sensor_stream(self, sensor_type: str, interval_ms: int = 1000, 
                           callback: Callable = None) -> bool:
        """Start continuous sensor data stream"""
        if callback:
            self.data_callbacks[f'RobotDataType.{sensor_type}'] = callback
        return self._send_command_sync('request', sensor_type, interval=interval_ms)
    
    def is_robot_online(self) -> bool:
        """Check if robot is online"""
        return self.robot_status.get('isConnected', False)
    
    # ============ SEQUENCE CONTROL METHODS ============
    
    def get_sequences(self) -> List[SequenceInfo]:
        """Get list of available sequences"""
        try:
            result = self._send_command_sync('command', 'sequence', 
                                           {'action': SequenceAction.LIST.value})
            if result:
                # Wait for response and parse sequences
                time.sleep(0.5)  # Give time for response
                seq_data = self.get_latest_sensor_data('sequence')
                if seq_data and 'data' in seq_data and 'sequences' in seq_data['data']:
                    sequences = []
                    for seq in seq_data['data']['sequences']:
                        sequences.append(SequenceInfo(
                            id=seq['id'],
                            name=seq['name'],
                            description=seq['description'],
                            step_count=seq['stepCount'],
                            duration=seq['duration'],
                            is_loop=seq['isLoop'],
                            created_at=seq['createdAt'],
                            component_usage=seq['componentUsage']
                        ))
                    return sequences
        except Exception as e:
            logger.error(f"Failed to get sequences: {e}")
        return []
    
    def play_sequence(self, sequence_name: str = None, sequence_id: str = None) -> bool:
        """Play a sequence by name or ID"""
        if not sequence_name and not sequence_id:
            logger.error("Either sequence_name or sequence_id must be provided")
            return False
        
        payload = {'action': SequenceAction.PLAY.value}
        if sequence_name:
            payload['name'] = sequence_name
        if sequence_id:
            payload['id'] = sequence_id
        
        return self._send_command_sync('command', 'sequence', payload)
    
    def stop_sequence(self) -> bool:
        """Stop current sequence playback"""
        payload = {'action': SequenceAction.STOP.value}
        return self._send_command_sync('command', 'sequence', payload)
    
    def pause_sequence(self) -> bool:
        """Pause current sequence playback"""
        payload = {'action': SequenceAction.PAUSE.value}
        return self._send_command_sync('command', 'sequence', payload)
    
    def resume_sequence(self) -> bool:
        """Resume paused sequence playback"""
        payload = {'action': SequenceAction.RESUME.value}
        return self._send_command_sync('command', 'sequence', payload)
    
    def jump_to_step(self, step_index: int) -> bool:
        """Jump to specific step in current sequence"""
        payload = {
            'action': SequenceAction.JUMPTO.value,
            'step': step_index
        }
        return self._send_command_sync('command', 'sequence', payload)
    
    def get_sequence_status(self) -> SequenceStatus:
        """Get current sequence status"""
        payload = {'action': SequenceAction.STATUS.value}
        self._send_command_sync('command', 'sequence', payload)
        return self.sequence_status
    
    # ============ CAMERA CONTROL METHODS ============
    
    def start_camera_stream(self) -> bool:
        """Start camera streaming"""
        payload = {'action': CameraAction.START.value}
        return self._send_command_sync('command', 'camera', payload)
    
    def stop_camera_stream(self) -> bool:
        """Stop camera streaming"""
        payload = {'action': CameraAction.STOP.value}
        return self._send_command_sync('command', 'camera', payload)
    
    def capture_image(self) -> Optional[CapturedImage]:
        """Capture a single image"""
        payload = {'action': CameraAction.CAPTURE.value}
        result = self._send_command_sync('command', 'camera', payload)
        if result:
            # Wait for response
            time.sleep(1)
            camera_data = self.get_latest_sensor_data('camera')
            if camera_data and 'data' in camera_data:
                data = camera_data['data']
                if 'imageData' in data:
                    return CapturedImage(
                        image_data=data['imageData'],
                        format=data.get('format', 'jpeg'),
                        timestamp=data.get('timestamp', datetime.now().isoformat())
                    )
        return None
    
    def get_camera_status(self) -> CameraStatus:
        """Get camera status"""
        payload = {'action': CameraAction.STATUS.value}
        self._send_command_sync('command', 'camera', payload)
        return self.camera_status
    
    def save_captured_image(self, captured_image: CapturedImage, filename: str):
        """Save captured image to file"""
        try:
            image_data = base64.b64decode(captured_image.image_data)
            with open(filename, 'wb') as f:
                f.write(image_data)
            logger.info(f"Image saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
    
    # ============ SPEAKING/TTS METHODS ============
    
    def speak(self, text: str) -> bool:
        """Make robot speak the given text"""
        if not text or not text.strip():
            logger.error("Text cannot be empty")
            return False
        
        payload = {'text': text.strip()}
        return self._send_command_sync('command', 'speak', payload)
    
    # ============ INDIVIDUAL SERVO CONTROL METHODS ============
    
    def control_right_gripper(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control right gripper servo"""
        return self.control_servo(ServoID.RIGHT_GRIPPER, angle, speed, acc)
    
    def control_right_wrist(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control right wrist servo"""
        return self.control_servo(ServoID.RIGHT_WRIST, angle, speed, acc)
    
    def control_right_elbow(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control right elbow servo"""
        return self.control_servo(ServoID.RIGHT_ELBOW, angle, speed, acc)
    
    def control_right_shoulder_pitch(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control right shoulder pitch servo"""
        return self.control_servo(ServoID.RIGHT_SHOULDER_PITCH, angle, speed, acc)
    
    def control_right_shoulder_yaw(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control right shoulder yaw servo"""
        return self.control_servo(ServoID.RIGHT_SHOULDER_YAW, angle, speed, acc)
    
    def control_right_shoulder_roll(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control right shoulder roll servo"""
        return self.control_servo(ServoID.RIGHT_SHOULDER_ROLL, angle, speed, acc)
    
    def control_left_gripper(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control left gripper servo"""
        return self.control_servo(ServoID.LEFT_GRIPPER, angle, speed, acc)
    
    def control_left_wrist(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control left wrist servo"""
        return self.control_servo(ServoID.LEFT_WRIST, angle, speed, acc)
    
    def control_left_elbow(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control left elbow servo"""
        return self.control_servo(ServoID.LEFT_ELBOW, angle, speed, acc)
    
    def control_left_shoulder_pitch(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control left shoulder pitch servo"""
        return self.control_servo(ServoID.LEFT_SHOULDER_PITCH, angle, speed, acc)
    
    def control_left_shoulder_yaw(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control left shoulder yaw servo"""
        return self.control_servo(ServoID.LEFT_SHOULDER_YAW, angle, speed, acc)
    
    def control_left_shoulder_roll(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control left shoulder roll servo"""
        return self.control_servo(ServoID.LEFT_SHOULDER_ROLL, angle, speed, acc)
    
    def control_head_pan(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control head pan servo"""
        return self.control_servo(ServoID.HEAD_PAN, angle, speed, acc)
    
    def control_head_tilt(self, angle: float, speed: float = None, acc: float = None) -> bool:
        """Control head tilt servo"""
        return self.control_servo(ServoID.HEAD_TILT, angle, speed, acc)
    
    # ============ COMPOSITE CONTROL METHODS ============
    
    def control_head_composite(self, head_cmd: HeadCommand) -> bool:
        """Control robot head with HeadCommand object"""
        payload = {
            'tilt': head_cmd.tilt,
            'pan': head_cmd.pan,
            'mode': head_cmd.mode.value,
            'speed': head_cmd.speed,
            'acceleration': head_cmd.acceleration
        }
        return self._send_command_sync('command', 'head', payload)
    
    def control_left_hand_composite(self, hand_cmd: HandCommand) -> bool:
        """Control left hand with HandCommand object"""
        payload = {
            'sholderPitchServo': {'currentAngle': hand_cmd.shoulder_pitch, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'sholderYawServo': {'currentAngle': hand_cmd.shoulder_yaw, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'sholderRollServo': {'currentAngle': hand_cmd.shoulder_roll, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'elbowServo': {'currentAngle': hand_cmd.elbow, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'wristServo': {'currentAngle': hand_cmd.wrist, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'gripperServo': {'currentAngle': hand_cmd.gripper, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration}
        }
        return self._send_command_sync('command', 'lefthand', payload)
    
    def control_right_hand_composite(self, hand_cmd: HandCommand) -> bool:
        """Control right hand with HandCommand object"""
        payload = {
            'sholderPitchServo': {'currentAngle': hand_cmd.shoulder_pitch, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'sholderYawServo': {'currentAngle': hand_cmd.shoulder_yaw, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'sholderRollServo': {'currentAngle': hand_cmd.shoulder_roll, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'elbowServo': {'currentAngle': hand_cmd.elbow, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'wristServo': {'currentAngle': hand_cmd.wrist, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration},
            'gripperServo': {'currentAngle': hand_cmd.gripper, 'currentSpeed': hand_cmd.speed, 'acceleration': hand_cmd.acceleration}
        }
        return self._send_command_sync('command', 'righthand', payload)
    
    def control_base_composite(self, base_cmd: BaseCommand) -> bool:
        """Control robot base with BaseCommand object"""
        payload = {
            'leftMotor': {'currentSpeed': base_cmd.left_motor_speed, 'type': base_cmd.motor_type.value},
            'rightMotor': {'currentSpeed': base_cmd.right_motor_speed, 'type': base_cmd.motor_type.value}
        }
        return self._send_command_sync('command', 'base', payload)
    
    # ============ SINGLE SENSOR READING METHODS ============
    
    def read_battery(self) -> bool:
        """Read battery status once"""
        return self._send_command_sync('request', 'battery')
    
    def read_left_hand_sensors(self) -> bool:
        """Read left hand sensor data once"""
        return self._send_command_sync('request', 'lefthand')
    
    def read_right_hand_sensors(self) -> bool:
        """Read right hand sensor data once"""
        return self._send_command_sync('request', 'righthand')
    
    def read_head_sensors(self) -> bool:
        """Read head sensor data once"""
        return self._send_command_sync('request', 'head')
    
    def read_base_sensors(self) -> bool:
        """Read base sensor data once"""
        return self._send_command_sync('request', 'base')
    
    def read_distance(self) -> bool:
        """Read distance sensor once"""
        return self._send_command_sync('request', 'distance')
    
    # ============ CONTINUOUS DATA STREAMING METHODS ============
    
    def start_battery_stream(self, interval_ms: int = 1000, 
                            callback: Callable[[Dict], None] = None) -> bool:
        """Start continuous battery data stream"""
        if callback:
            self.data_callbacks['RobotDataType.battery'] = callback
        return self._send_command_sync('request', 'battery', interval=interval_ms)
    
    def start_left_hand_stream(self, interval_ms: int = 100, 
                              callback: Callable[[Dict], None] = None) -> bool:
        """Start continuous left hand sensor stream"""
        if callback:
            self.data_callbacks['RobotDataType.leftHand'] = callback
        return self._send_command_sync('request', 'lefthand', interval=interval_ms)
    
    def start_right_hand_stream(self, interval_ms: int = 100, 
                               callback: Callable[[Dict], None] = None) -> bool:
        """Start continuous right hand sensor stream"""
        if callback:
            self.data_callbacks['RobotDataType.rightHand'] = callback
        return self._send_command_sync('request', 'righthand', interval=interval_ms)
    
    def start_head_stream(self, interval_ms: int = 100, 
                         callback: Callable[[Dict], None] = None) -> bool:
        """Start continuous head sensor stream"""
        if callback:
            self.data_callbacks['RobotDataType.head'] = callback
        return self._send_command_sync('request', 'head', interval=interval_ms)
    
    def start_base_stream(self, interval_ms: int = 100, 
                         callback: Callable[[Dict], None] = None) -> bool:
        """Start continuous base sensor stream"""
        if callback:
            self.data_callbacks['RobotDataType.base'] = callback
        return self._send_command_sync('request', 'base', interval=interval_ms)
    
    def start_distance_stream(self, interval_ms: int = 200, 
                             callback: Callable[[Dict], None] = None) -> bool:
        """Start continuous distance sensor stream"""
        if callback:
            self.data_callbacks['RobotDataType.distance'] = callback
        return self._send_command_sync('request', 'distance', interval=interval_ms)
    
    # ============ ADVANCED SENSOR DATA ACCESS METHODS ============
    
    def unregister_sensor_listener(self, sensor_type: str, listener_id: str) -> bool:
        """Unregister a sensor listener"""
        if (sensor_type in self.sensor_listeners and 
            listener_id in self.sensor_listeners[sensor_type]):
            del self.sensor_listeners[sensor_type][listener_id]
            logger.info(f"Unregistered listener {listener_id} for {sensor_type}")
            return True
        return False
    
    def register_error_callback(self, command_type: str, data_type: str, callback: Callable):
        """Register callback for command errors"""
        error_key = f"{command_type}_{data_type}"
        self.error_callbacks[error_key] = callback
    
    def get_sensor_history(self, sensor_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical sensor data"""
        if sensor_type in self.sensor_history:
            return self.sensor_history[sensor_type][-limit:]
        return []
    
    def get_hand_servo_readings(self, is_right: bool = True) -> Dict[str, ServoReading]:
        """Get parsed servo readings for a hand"""
        sensor_type = 'right_hand' if is_right else 'left_hand'
        data = self.get_latest_sensor_data(sensor_type)
        servos = {}
        
        if data and data['data']:
            hand_data = data['data']
            
            # Parse each servo
            servo_names = [
                'gripperServo', 'wristServo', 'elbowServo',
                'sholderPitchServo', 'sholderYawServo', 'sholderRollServo'
            ]
            
            for servo_name in servo_names:
                if servo_name in hand_data:
                    servo_data = hand_data[servo_name]
                    servos[servo_name] = ServoReading(
                        id=servo_data.get('id', ''),
                        name=servo_data.get('name', servo_name),
                        feedback_angle=servo_data.get('feedbackAngle', 0),
                        feedback_speed=servo_data.get('feedbackSpeed', 0),
                        load=servo_data.get('load', 0),
                        temperature=servo_data.get('temperature', 0),
                        has_error=servo_data.get('hasError', False)
                    )
        
        return servos
    
    def get_head_servo_readings(self) -> Dict[str, ServoReading]:
        """Get parsed head servo readings"""
        data = self.get_latest_sensor_data('head')
        servos = {}
        
        if data and data['data']:
            head_data = data['data']
            
            # Parse pan and tilt servos
            for servo_name in ['panServo', 'tiltServo']:
                if servo_name in head_data:
                    servo_data = head_data[servo_name]
                    servos[servo_name] = ServoReading(
                        id=servo_data.get('id', ''),
                        name=servo_data.get('name', servo_name),
                        feedback_angle=servo_data.get('feedbackAngle', 0),
                        feedback_speed=servo_data.get('feedbackSpeed', 0),
                        load=servo_data.get('load', 0),
                        temperature=servo_data.get('temperature', 0),
                        has_error=servo_data.get('hasError', False)
                    )
        
        return servos
    
    def get_base_motor_readings(self) -> Dict[str, MotorReading]:
        """Get parsed base motor readings"""
        data = self.get_latest_sensor_data('base')
        motors = {}
        
        if data and data['data']:
            base_data = data['data']
            
            for motor_name in ['leftMotor', 'rightMotor']:
                if motor_name in base_data:
                    motor_data = base_data[motor_name]
                    motors[motor_name] = MotorReading(
                        id=motor_data.get('id', motor_name),
                        feedback_speed=motor_data.get('feedbackSpeed', 0),
                        feedback_position=motor_data.get('feedbackPosition', 0),
                        torque=motor_data.get('torque', 0),
                        temperature=motor_data.get('temperature', 0),
                        mode=motor_data.get('mode', 0),
                        has_error=motor_data.get('hasError', False)
                    )
        
        return motors
    
    def is_sensor_data_recent(self, sensor_type: str, max_age_seconds: float = 5.0) -> bool:
        """Check if sensor data is recent"""
        data = self.get_latest_sensor_data(sensor_type)
        if data and 'timestamp' in data:
            age = (datetime.now() - data['timestamp']).total_seconds()
            return age <= max_age_seconds
        return False
    
    def get_sensor_data_age(self, sensor_type: str) -> Optional[float]:
        """Get the age of sensor data in seconds"""
        data = self.get_latest_sensor_data(sensor_type)
        if data and 'timestamp' in data:
            return (datetime.now() - data['timestamp']).total_seconds()
        return None
    
    def monitor_servo_temperature(self, threshold: float = 60.0, 
                                callback: Callable[[str, float], None] = None):
        """Monitor servo temperatures and call callback if threshold exceeded"""
        def temp_filter(data):
            # Check all servos in the data
            for key, value in data.items():
                if isinstance(value, dict) and 'temperature' in value:
                    temp = value['temperature']
                    if temp > threshold:
                        servo_name = value.get('name', key)
                        if callback:
                            callback(servo_name, temp)
                        logger.warning(f"Servo {servo_name} temperature high: {temp}°C")
                        return True
            return False
        
        # Register for all hand and head sensors
        self.register_sensor_listener('left_hand', 'temp_monitor_left', 
                                    lambda data: None, temp_filter)
        self.register_sensor_listener('right_hand', 'temp_monitor_right', 
                                    lambda data: None, temp_filter)
        self.register_sensor_listener('head', 'temp_monitor_head', 
                                    lambda data: None, temp_filter)
    
    def monitor_battery_level(self, low_threshold: float = 20.0, 
                            callback: Callable[[float], None] = None):
        """Monitor battery level and call callback if below threshold"""
        def battery_filter(data):
            soc = data.get('soc', 100)
            if soc <= low_threshold:
                if callback:
                    callback(soc)
                logger.warning(f"Battery level low: {soc}%")
                return True
            return False
        
        self.register_sensor_listener('battery', 'battery_monitor', 
                                    lambda data: None, battery_filter)
    
    def monitor_servo_errors(self, callback: Callable[[str, Dict], None] = None):
        """Monitor for servo errors"""
        def error_filter(data):
            for key, value in data.items():
                if isinstance(value, dict) and value.get('hasError', False):
                    servo_name = value.get('name', key)
                    if callback:
                        callback(servo_name, value)
                    logger.error(f"Servo error detected: {servo_name}")
                    return True
            return False
        
        # Register for all servo sensors
        sensor_types = ['left_hand', 'right_hand', 'head']
        for sensor_type in sensor_types:
            self.register_sensor_listener(sensor_type, f'error_monitor_{sensor_type}', 
                                        lambda data: None, error_filter)
    
    def start_comprehensive_monitoring(self, callbacks: Dict[str, Callable] = None):
        """Start comprehensive sensor monitoring with optional callbacks"""
        callbacks = callbacks or {}
        
        # Start temperature monitoring
        temp_callback = callbacks.get('temperature')
        self.monitor_servo_temperature(callback=temp_callback)
        
        # Start battery monitoring
        battery_callback = callbacks.get('battery')
        self.monitor_battery_level(callback=battery_callback)
        
        # Start error monitoring
        error_callback = callbacks.get('errors')
        self.monitor_servo_errors(callback=error_callback)
        
        logger.info("Comprehensive sensor monitoring started")
    
    def clear_all_listeners(self):
        """Clear all registered sensor listeners"""
        self.sensor_listeners.clear()
        logger.info("All sensor listeners cleared")
    
    def get_sensor_summary(self) -> Dict[str, Any]:
        """Get a summary of all current sensor data"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'robot_connected': self.is_robot_online(),
            'sequence_status': asdict(self.sequence_status),
            'camera_status': asdict(self.camera_status),
            'sensors': {}
        }
        
        for sensor_type in self.latest_sensor_data:
            data = self.get_latest_sensor_data(sensor_type)
            if data:
                age = self.get_sensor_data_age(sensor_type)
                summary['sensors'][sensor_type] = {
                    'has_data': True,
                    'age_seconds': age,
                    'is_recent': self.is_sensor_data_recent(sensor_type),
                    'data_size': len(str(data['data'])) if data.get('data') else 0
                }
            else:
                summary['sensors'][sensor_type] = {
                    'has_data': False,
                    'age_seconds': None,
                    'is_recent': False,
                    'data_size': 0
                }
        
        return summary
    
    # ============ CONVENIENCE MOVEMENT METHODS ============
    
    def set_head_mode(self, mode: HeadModes) -> bool:
        """Set head expression mode"""
        head_cmd = HeadCommand(mode=mode)
        return self.control_head_composite(head_cmd)
    
    def open_gripper(self, is_right: bool = True, speed: float = None):
        """Open gripper"""
        angle = 90.0 if is_right else -90.0
        if is_right:
            return self.control_right_gripper(angle, speed)
        else:
            return self.control_left_gripper(angle, speed)
    
    def close_gripper(self, is_right: bool = True, speed: float = None):
        """Close gripper"""
        angle = -90.0 if is_right else 90.0
        if is_right:
            return self.control_right_gripper(angle, speed)
        else:
            return self.control_left_gripper(angle, speed)
    
    # ============ HIGH-LEVEL CONVENIENCE METHODS ============
    
    def wave_hello(self, use_right_hand: bool = True, speed: float = 150.0) -> bool:
        """Perform a simple wave gesture"""
        if use_right_hand:
            # Right hand wave
            self.control_right_shoulder_pitch(90, speed)
            time.sleep(0.5)
            for _ in range(3):
                self.control_right_wrist(45, speed)
                time.sleep(0.3)
                self.control_right_wrist(-45, speed)
                time.sleep(0.3)
            self.control_right_wrist(0, speed)
            self.control_right_shoulder_pitch(0, speed)
        else:
            # Left hand wave  
            self.control_left_shoulder_pitch(90, speed)
            time.sleep(0.5)
            for _ in range(3):
                self.control_left_wrist(45, speed)
                time.sleep(0.3)
                self.control_left_wrist(-45, speed)
                time.sleep(0.3)
            self.control_left_wrist(0, speed)
            self.control_left_shoulder_pitch(0, speed)
        return True
    
    def look_around(self, speed: float = 100.0) -> bool:
        """Look around by moving head"""
        positions = [(-45, 0), (45, 0), (0, 30), (0, -30), (0, 0)]
        for pan, tilt in positions:
            self.control_head_pan(pan, speed)
            self.control_head_tilt(tilt, speed)
            time.sleep(1)
        return True
    
    def reset_to_home_position(self, speed: float = 100.0) -> bool:
        """Reset all servos to home position (0 degrees)"""
        # Head to center
        self.control_head_pan(0, speed)
        self.control_head_tilt(0, speed)

    
        
        # Both hands to neutral
        for side in ['left', 'right']:
            if side == 'right':
                self.control_right_shoulder_pitch(0, speed)
                self.control_right_shoulder_yaw(0, speed)
                self.control_right_shoulder_roll(0, speed)
                self.control_right_elbow(0, speed)
                self.control_right_wrist(0, speed)
                self.control_right_gripper(0, speed)
            else:
                self.control_left_shoulder_pitch(0, speed)
                self.control_left_shoulder_yaw(0, speed)
                self.control_left_shoulder_roll(0, speed)
                self.control_left_elbow(0, speed)
                self.control_left_wrist(0, speed)
                self.control_left_gripper(0, speed)
        
        # Stop base movement
        self.stop_movement()
        
        return True

# ============ FACTORY FUNCTIONS ============

def create_serial_controller(port: str, baudrate: int = 115200, 
                           timeout: float = 1.0) -> SerialBonicBotController:
    """Create a serial BonicBot controller"""
    return SerialBonicBotController(port, baudrate, timeout)

def create_websocket_controller(host: str = "localhost", 
                              port: int = 8080) -> WebSocketBonicBotController:
    """Create a WebSocket BonicBot controller"""
    return WebSocketBonicBotController(host, port)

# ============ LEGACY COMPATIBILITY ============

# Maintain backward compatibility by making BonicBotController default to serial
def BonicBotController(port_or_host: str, baudrate_or_port: Union[int, None] = None, 
                      timeout: float = 1.0, communication_type: CommunicationType = None):
    """
    Create a BonicBot controller with automatic type detection.
    
    Args:
        port_or_host: Serial port (e.g., '/dev/ttyUSB0') or WebSocket host
        baudrate_or_port: Baudrate for serial or port for WebSocket
        timeout: Connection timeout
        communication_type: Force specific communication type
    
    Returns:
        Appropriate controller instance
    """
    # Auto-detect communication type if not specified
    if communication_type is None:
        if isinstance(baudrate_or_port, int) and baudrate_or_port > 1000:
            # Looks like a baudrate, assume serial
            communication_type = CommunicationType.SERIAL
        elif baudrate_or_port is None and '/' in port_or_host:
            # Looks like a file path, assume serial
            communication_type = CommunicationType.SERIAL
        else:
            # Assume WebSocket
            communication_type = CommunicationType.WEBSOCKET
    
    if communication_type == CommunicationType.SERIAL:
        baudrate = baudrate_or_port or 115200
        return SerialBonicBotController(port_or_host, baudrate, timeout)
    else:
        port = baudrate_or_port or 8080
        return WebSocketBonicBotController(port_or_host, port)