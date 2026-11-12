USE ip_project2022;

INSERT IGNORE INTO stocks
    (BatchNo, ExpiryDate, NameofMedicine, Quantity, Price, CostPrice,
     ManufacturerName, ManufacturerPhoneNo, MfgDate)
VALUES
    ('DEMO001', DATE_ADD(CURDATE(), INTERVAL 365 DAY), 'Sample Pain Relief', 18,
     12.00, 7.00, 'Example Manufacturer', '0000000000',
     DATE_SUB(CURDATE(), INTERVAL 30 DAY)),
    ('DEMO002', DATE_ADD(CURDATE(), INTERVAL 500 DAY), 'Sample Vitamin', 40,
     20.00, 13.00, 'Example Manufacturer', '0000000000',
     DATE_SUB(CURDATE(), INTERVAL 20 DAY));

INSERT IGNORE INTO staffinfo
    (EmpNo, Name, Gender, Age, Designation, Salary, AdharNo, Doj)
VALUES
    ('DEMO-EMP-1', 'Demo Employee', 'Not specified', 25, 'Assistant',
     15000.00, '000000000000', CURDATE());

INSERT IGNORE INTO customerinformation
    (ID, NAME, GENDER, AGE, PhoneNumber, ReceiptNumber, DoctorName,
     Address, ReasonForVisit)
VALUES
    ('DEMO-CUST-1', 'Demo Customer', 'Not specified', 30, '0000000000',
     'DEMO-0001', NULL, 'Demo address', 'Demo record');

INSERT IGNORE INTO bills
    (ReceiptNumber, DATEOFBILL, CustomerID, CustomerName, CustomerPhone,
     Subtotal, GSTRate, GSTAmount, Total)
VALUES
    ('DEMO-0001', NOW(), 'DEMO-CUST-1', 'Demo Customer', '0000000000',
     24.00, 5.00, 1.20, 25.20);

INSERT IGNORE INTO bill_items
    (BillID, BatchNo, MedicineName, BillQuantity, UnitPrice, UnitCost, LineTotal)
SELECT BillID, 'DEMO001', 'Sample Pain Relief', 2, 12.00, 7.00, 24.00
FROM bills
WHERE ReceiptNumber = 'DEMO-0001';

INSERT IGNORE INTO expenses (ExpenseDate, Category, Amount, Description)
VALUES (CURDATE(), 'Demo expense', 2.00, 'Fictional example for graph testing');
