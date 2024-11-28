# pid_controller.py
class PIDController:
    def __init__(self, kp, ki, kd, output_limits=(-1.0, 1.0)):
        self.kp = kp  # Proportional gain
        self.ki = ki  # Integral gain
        self.kd = kd  # Derivative gain
        self.output_limits = output_limits  # Tuple (min_output, max_output)

        self._last_error = 0.0
        self._integral = 0.0

    def update(self, error, dt):
        # Proportional term
        p = self.kp * error

        # Integral term
        self._integral += error * dt
        i = self.ki * self._integral

        # Derivative term
        derivative = (error - self._last_error) / dt if dt > 0 else 0.0
        d = self.kd * derivative

        # Total output
        output = p + i + d

        # Clamp output to limits
        min_output, max_output = self.output_limits
        output = max(min(output, max_output), min_output)

        # Save error for next derivative calculation
        self._last_error = error

        return output
