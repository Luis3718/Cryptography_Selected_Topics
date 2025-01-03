from sqlalchemy.orm import Session
from fastapi import HTTPException
import models, schemas
from fpe import encrypt_card_number, generate_salt  # Importa el módulo FPE y generación de Salt
from custom_hashing import hash_password
from ECDSA import generate_ecdsa_keys

def create_employee(db: Session, employee: schemas.EmployeeCreate):
    # Generar un Salt único para FPE
    employee.Salt = generate_salt()
    
    # Hashear la contraseña
    employee.PasswordHash = hash_password(employee.PasswordHash)

    # Generar las llaves ECDSA
    private_key, public_key = generate_ecdsa_keys()
    employee.PublicKeyECDSA = public_key  # Guardar la llave pública en la base de datos

    # Crear la entrada en la base de datos
    db_employee = models.Employee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    # Guardar la llave privada en un archivo
    file_path = f"private_keys/private_key_{db_employee.EmployeeID}.pem"
    with open(file_path, "w") as key_file:
        key_file.write(private_key)

    return db_employee, file_path  # Retornar el archivo generado


def create_customer(db: Session, customer: schemas.CustomerCreate):
    # Generar un Salt único para FPE
    customer.Salt = generate_salt()

    # Cifrar el número de tarjeta de crédito con FPE
    customer.CreditCardNumber = encrypt_card_number(
        card_number=customer.CreditCardNumber,
        password=customer.Username,  # Usa un dato relacionado con el usuario
        salt=customer.Salt
    )

    # Hashear la contraseña
    customer.PasswordHash = hash_password(customer.PasswordHash)
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customer_id_from_token(token: str) -> int:
    import jwt
    from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

    SECRET_KEY = "your_secret_key"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        customer_id = payload.get("id")
        if not customer_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return customer_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_employee_id_from_token(token: str) -> dict:
    import jwt
    from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

    SECRET_KEY = "your_secret_key"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        role = payload.get("role")
        employee_id = payload.get("id")
        if not role or not employee_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"role": role, "id": employee_id}
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
