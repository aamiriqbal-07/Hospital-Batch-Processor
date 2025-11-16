import csv
import io
from typing import List, Dict, Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.utils.exceptions import CSVValidationException


class CSVValidator:
    """CSV file validator"""
    
    @staticmethod
    async def validate_and_parse(file: UploadFile) -> Tuple[List[Dict[str, str]], List[dict]]:
        errors = []
        
        # Read file content
        try:
            content = await file.read()
            decoded_content = content.decode('utf-8')
        except UnicodeDecodeError:
            errors.append({
                "loc": ["file", "encoding"],
                "msg": "File must be UTF-8 encoded",
                "type": "encoding_error"
            })
            raise CSVValidationException(errors)
        finally:
            await file.seek(0)
        
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.CSV_MAX_SIZE_MB:
            errors.append({
                "loc": ["file", "size"],
                "msg": f"File size exceeds {settings.CSV_MAX_SIZE_MB}MB limit",
                "type": "file_size_error"
            })
            raise CSVValidationException(errors)
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        # Validate headers
        if not csv_reader.fieldnames:
            errors.append({
                "loc": ["file", "headers"],
                "msg": "CSV file has no headers",
                "type": "missing_headers"
            })
            raise CSVValidationException(errors)

        expected_headers = settings.CSV_REQUIRED_HEADERS
        if list(csv_reader.fieldnames) != expected_headers:
            errors.append({
                "loc": ["file", "headers"],
                "msg": f"CSV headers must be exactly: {','.join(expected_headers)} (case-sensitive)",
                "type": "invalid_headers"
            })
            raise CSVValidationException(errors)

        parsed_rows = []
        row_number = 1
        
        for row in csv_reader:
            row_number += 1
            row_errors = CSVValidator._validate_row(row, row_number)
            
            if row_errors:
                errors.extend(row_errors)
            else:
                if row.get('phone') == '':
                    row['phone'] = None
                parsed_rows.append(row)

        if not parsed_rows and not errors:
            errors.append({
                "loc": ["file", "content"],
                "msg": "CSV file contains no data rows",
                "type": "empty_file"
            })
        
        if errors:
            raise CSVValidationException(errors)
        
        return parsed_rows, []
    
    @staticmethod
    def _validate_row(row: Dict[str, str], row_number: int) -> List[dict]:
        errors = []
        
        name = row.get('name', '').strip()
        if not name:
            errors.append({
                "loc": ["row", row_number, "name"],
                "msg": "name is required and must be at least 1 character",
                "type": "value_error"
            })

        address = row.get('address', '').strip()
        if not address:
            errors.append({
                "loc": ["row", row_number, "address"],
                "msg": "address is required and must be at least 1 character",
                "type": "value_error"
            })
        
        return errors
