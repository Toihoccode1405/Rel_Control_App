"""
kRel - Input Validation Service
Centralized validation with clear error messages
"""
import re
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Any, Dict


@dataclass
class ValidationError:
    """Represents a single validation error"""
    field: str
    message: str
    value: Any = None


@dataclass
class ValidationResult:
    """Result of validation containing all errors"""
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, field: str, message: str, value: Any = None):
        self.errors.append(ValidationError(field, message, value))

    def get_error(self, field: str) -> Optional[str]:
        """Get first error message for a field"""
        for err in self.errors:
            if err.field == field:
                return err.message
        return None

    def get_all_messages(self) -> List[str]:
        """Get all error messages"""
        return [f"{e.field}: {e.message}" for e in self.errors]

    def to_html(self) -> str:
        """Format errors as HTML for display"""
        if self.is_valid:
            return ""
        lines = ["<b>Vui lòng kiểm tra:</b><ul>"]
        for err in self.errors:
            lines.append(f"<li><b>{err.field}</b>: {err.message}</li>")
        lines.append("</ul>")
        return "".join(lines)


class FieldValidator:
    """Fluent validator for a single field"""

    def __init__(self, field_name: str, value: Any, label: str = None):
        self.field = field_name
        self.label = label or field_name
        self.value = value
        self.errors: List[str] = []
        self._stop = False

    def required(self, message: str = None) -> "FieldValidator":
        """Value must not be empty"""
        if self._stop:
            return self
        if self.value is None or (isinstance(self.value, str) and not self.value.strip()):
            self.errors.append(message or "Không được để trống")
            self._stop = True
        return self

    def min_length(self, length: int, message: str = None) -> "FieldValidator":
        """String must have minimum length"""
        if self._stop or not isinstance(self.value, str):
            return self
        if len(self.value.strip()) < length:
            self.errors.append(message or f"Tối thiểu {length} ký tự")
        return self

    def max_length(self, length: int, message: str = None) -> "FieldValidator":
        """String must not exceed maximum length"""
        if self._stop or not isinstance(self.value, str):
            return self
        if len(self.value.strip()) > length:
            self.errors.append(message or f"Tối đa {length} ký tự")
        return self

    def pattern(self, regex: str, message: str = None) -> "FieldValidator":
        """Value must match regex pattern"""
        if self._stop or not isinstance(self.value, str):
            return self
        if not re.match(regex, self.value.strip()):
            self.errors.append(message or "Định dạng không hợp lệ")
        return self

    def numeric(self, message: str = None) -> "FieldValidator":
        """Value must be a number"""
        if self._stop:
            return self
        val = str(self.value).strip() if self.value else ""
        if val and not val.replace(".", "").replace("-", "").isdigit():
            self.errors.append(message or "Phải là số")
        return self

    def positive(self, message: str = None) -> "FieldValidator":
        """Numeric value must be positive"""
        if self._stop:
            return self
        try:
            if self.value and float(self.value) <= 0:
                self.errors.append(message or "Phải lớn hơn 0")
        except (ValueError, TypeError):
            pass
        return self

    def email(self, message: str = None) -> "FieldValidator":
        """Value must be valid email format"""
        if self._stop or not isinstance(self.value, str):
            return self
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if self.value.strip() and not re.match(pattern, self.value.strip()):
            self.errors.append(message or "Email không hợp lệ")
        return self

    def in_list(self, valid_values: List[Any], message: str = None) -> "FieldValidator":
        """Value must be in allowed list"""
        if self._stop:
            return self
        if self.value and self.value not in valid_values:
            self.errors.append(message or f"Giá trị không hợp lệ")
        return self


class Validator:
    """Main validator class - fluent interface for validation"""

    # Field labels for Vietnamese display
    FIELD_LABELS = {
        "request_no": "Mã yêu cầu",
        "request_date": "Ngày yêu cầu",
        "requester": "Người yêu cầu",
        "factory": "Nhà máy",
        "project": "Dự án",
        "phase": "Giai đoạn",
        "category": "Hạng mục",
        "equip_no": "Mã thiết bị",
        "equip_name": "Tên thiết bị",
        "qty": "Số lượng",
        "test_condition": "Điều kiện test",
        "status": "Trạng thái",
        "dri": "Người phụ trách",
        "username": "Tên đăng nhập",
        "password": "Mật khẩu",
        "fullname": "Họ và tên",
        "email": "Email",
    }

    def __init__(self):
        self.result = ValidationResult()
        self._validators: List[FieldValidator] = []

    def field(self, name: str, value: Any, label: str = None) -> FieldValidator:
        """Start validating a field"""
        display_label = label or self.FIELD_LABELS.get(name, name)
        validator = FieldValidator(name, value, display_label)
        self._validators.append(validator)
        return validator

    def validate(self) -> ValidationResult:
        """Execute all validations and return result"""
        for v in self._validators:
            if v.errors:
                for msg in v.errors:
                    self.result.add_error(v.label, msg, v.value)
        return self.result


# ============ Pre-built Validators ============

class RequestValidator:
    """Validator for Request form"""

    @staticmethod
    def validate_create(data: Dict[str, Any]) -> ValidationResult:
        """Validate data for creating new request"""
        v = Validator()

        v.field("request_no", data.get("request_no")).required().pattern(
            r"^\d{8}-\d{3}$", "Định dạng: YYYYMMDD-SSS"
        )
        v.field("request_date", data.get("request_date")).required()
        v.field("requester", data.get("requester")).required().min_length(2)
        v.field("factory", data.get("factory")).required()
        v.field("project", data.get("project")).required()
        v.field("qty", data.get("qty")).numeric().positive()

        return v.validate()

    @staticmethod
    def validate_update(data: Dict[str, Any]) -> ValidationResult:
        """Validate data for updating request"""
        v = Validator()

        v.field("request_no", data.get("request_no")).required()
        v.field("requester", data.get("requester")).required()

        return v.validate()


class UserValidator:
    """Validator for User registration/login"""

    @staticmethod
    def validate_register(username: str, password: str,
                          fullname: str, email: str) -> ValidationResult:
        """Validate registration data"""
        v = Validator()

        v.field("username", username).required().min_length(3).max_length(50).pattern(
            r"^[a-zA-Z0-9_]+$", "Chỉ chữ, số và dấu gạch dưới"
        )
        v.field("password", password).required().min_length(4)
        v.field("fullname", fullname).required().min_length(2).max_length(100)
        v.field("email", email).email()

        return v.validate()

    @staticmethod
    def validate_login(username: str, password: str) -> ValidationResult:
        """Validate login data"""
        v = Validator()

        v.field("username", username).required()
        v.field("password", password).required()

        return v.validate()


# Singleton access
_validator_instance = None

def get_validator() -> Validator:
    """Get new validator instance"""
    return Validator()


class FormValidator:
    """
    Helper class for form validation with inline error display.
    Works with ValidatedField widgets.
    """

    def __init__(self, fields: dict):
        """
        Initialize with dict of field_name -> ValidatedField widget
        """
        self.fields = fields
        self._validation_rules = {}

    def add_rule(self, field_name: str, validator_fn, error_msg: str):
        """
        Add validation rule for a field.
        validator_fn: callable(value) -> bool
        """
        if field_name not in self._validation_rules:
            self._validation_rules[field_name] = []
        self._validation_rules[field_name].append((validator_fn, error_msg))
        return self

    def required(self, field_name: str, message: str = None):
        """Add required rule"""
        msg = message or "Không được để trống"
        return self.add_rule(
            field_name,
            lambda v: bool(v and str(v).strip()),
            msg
        )

    def min_length(self, field_name: str, length: int, message: str = None):
        """Add min length rule"""
        msg = message or f"Tối thiểu {length} ký tự"
        return self.add_rule(
            field_name,
            lambda v: len(str(v).strip()) >= length if v else True,
            msg
        )

    def pattern(self, field_name: str, regex: str, message: str = None):
        """Add pattern rule"""
        import re
        msg = message or "Định dạng không hợp lệ"
        return self.add_rule(
            field_name,
            lambda v: bool(re.match(regex, str(v).strip())) if v else True,
            msg
        )

    def numeric(self, field_name: str, message: str = None):
        """Add numeric rule"""
        msg = message or "Phải là số"
        def check(v):
            if not v:
                return True
            try:
                float(str(v).strip())
                return True
            except ValueError:
                return False
        return self.add_rule(field_name, check, msg)

    def validate_field(self, field_name: str) -> bool:
        """Validate single field and show/clear error"""
        if field_name not in self.fields:
            return True

        field_widget = self.fields[field_name]
        value = field_widget.get_value() if hasattr(field_widget, 'get_value') else ""

        rules = self._validation_rules.get(field_name, [])
        for validator_fn, error_msg in rules:
            if not validator_fn(value):
                if hasattr(field_widget, 'show_error'):
                    field_widget.show_error(error_msg)
                return False

        if hasattr(field_widget, 'clear_error'):
            field_widget.clear_error()
        return True

    def validate_all(self) -> bool:
        """Validate all fields and return True if all valid"""
        all_valid = True
        first_error_field = None

        for field_name in self._validation_rules:
            if not self.validate_field(field_name):
                all_valid = False
                if first_error_field is None:
                    first_error_field = field_name

        # Focus first error field
        if first_error_field and first_error_field in self.fields:
            self.fields[first_error_field].setFocus()

        return all_valid

    def clear_all_errors(self):
        """Clear all field errors"""
        for field in self.fields.values():
            if hasattr(field, 'clear_error'):
                field.clear_error()

