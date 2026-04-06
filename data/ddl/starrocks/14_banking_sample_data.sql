-- =============================================================================
-- DataPrismAI Banking Platform
-- File: 14_banking_sample_data.sql
-- Purpose: Representative sample data across SG, MY, IN
-- Note: Load raw tables first, then DDM, then DP/Semantic
-- =============================================================================

-- =============================================================================
-- RAW LAYER SAMPLE DATA
-- =============================================================================

-- raw_customer
INSERT INTO raw_customer VALUES
('CUST001', 'SG', 'SG_BANK', 'Wei',    'Tan',      '1985-03-15', 'M', 'wei.tan@email.sg',    '+6591234567', '10 Orchard Rd #05-01', 'Singapore', NULL,      '238803', 'Singaporean', 'NRIC',     'S8500123A', 'AFFLUENT', 'VERIFIED', 'LOW',    125000.00, 'SGD', 'Finance Manager',       'BRANCH',  'CBS', 0, '2018-06-01 09:00:00', '2025-01-15 10:30:00'),
('CUST002', 'SG', 'SG_BANK', 'Priya',  'Nair',     '1992-07-22', 'F', 'priya.n@email.sg',    '+6598765432', '25 Bishan St #12-05',  'Singapore', NULL,      '570025', 'Singaporean', 'NRIC',     'S9200456B', 'MASS',     'VERIFIED', 'LOW',     48000.00, 'SGD', 'Teacher',               'ONLINE',  'CBS', 0, '2020-03-10 14:00:00', '2025-02-01 09:00:00'),
('CUST003', 'SG', 'SG_BANK', 'Ahmad',  'Ridzwan',  '1978-11-30', 'M', 'ahmad.r@email.sg',    '+6582345678', '55 Clementi Ave 4',    'Singapore', NULL,      '129907', 'Singaporean', 'NRIC',     'S7800789C', 'PRIORITY', 'VERIFIED', 'MEDIUM', 280000.00, 'SGD', 'Business Owner',         'AGENT',   'CBS', 0, '2015-01-20 11:00:00', '2025-01-20 08:00:00'),
('CUST004', 'MY', 'MY_BANK', 'Raj',    'Kumar',    '1990-05-08', 'M', 'raj.kumar@email.my',  '+60123456789', 'No. 10 Jalan Ampang',  'Kuala Lumpur', 'Selangor', '50450', 'Malaysian', 'MYKAD',   '900508-10-1234', 'MASS', 'VERIFIED', 'LOW',   55000.00, 'MYR', 'Software Engineer',    'ONLINE',  'CTOS',0, '2019-08-15 10:00:00', '2025-01-10 11:00:00'),
('CUST005', 'MY', 'MY_BANK', 'Siti',   'Rahimah',  '1982-09-17', 'F', 'siti.r@email.my',     '+60198765432', '22 Jalan Bukit Bintang','Kuala Lumpur','Selangor','55100','Malaysian',  'MYKAD',   '820917-14-5678', 'AFFLUENT','VERIFIED', 'LOW',  180000.00, 'MYR', 'Doctor',               'BRANCH',  'CTOS',0, '2017-04-01 09:30:00', '2025-02-05 14:00:00'),
('CUST006', 'MY', 'MY_BANK', 'David',  'Lim',      '1975-12-03', 'M', 'david.lim@email.my',  '+60112345678', '88 Jalan Damansara',   'Petaling Jaya','Selangor','47400','Malaysian', 'MYKAD',   '751203-10-9999', 'HIGH_NET_WORTH','VERIFIED','LOW',850000.00,'MYR','Director',             'AGENT',   'CTOS',0, '2010-07-15 08:00:00', '2025-01-30 15:00:00'),
('CUST007', 'IN', 'IN_BANK', 'Ravi',   'Sharma',   '1988-04-25', 'M', 'ravi.s@email.in',     '+919876543210','C-12, Bandra West',    'Mumbai',    'Maharashtra','400050','Indian',   'AADHAR',  '9876 5432 1098',  'MASS', 'VERIFIED', 'LOW',    720000.00,'INR', 'IT Professional',      'ONLINE',  'CIBIL',0,'2021-01-15 12:00:00', '2025-01-25 09:00:00'),
('CUST008', 'IN', 'IN_BANK', 'Anita',  'Desai',    '1980-08-14', 'F', 'anita.d@email.in',    '+918765432109','Flat 302, Powai',       'Mumbai',    'Maharashtra','400076','Indian',   'PAN',     'ABCDE1234F',      'AFFLUENT','VERIFIED','MEDIUM',2400000.00,'INR','Business Owner',      'BRANCH',  'CIBIL',0,'2016-09-10 10:30:00', '2025-02-10 11:00:00'),
('CUST009', 'IN', 'IN_BANK', 'Vikram', 'Patel',    '1972-02-19', 'M', 'vikram.p@email.in',   '+917654321098','15, MG Road',          'Bangalore', 'Karnataka','560001','Indian',    'AADHAR',  '8765 4321 0987',  'PRIORITY','VERIFIED','LOW',   5800000.00,'INR','CEO',                  'AGENT',   'CIBIL',0,'2012-06-01 08:00:00', '2025-01-05 16:00:00'),
('CUST010', 'SG', 'SG_BANK', 'Emily',  'Ong',      '1995-10-11', 'F', 'emily.o@email.sg',    '+6577889900',  '8 Toa Payoh Ctrl #08-12','Singapore',NULL,     '310008', 'Singaporean','NRIC',    'S9501011D', 'MASS',     'PENDING',  'HIGH',    32000.00,'SGD', 'Freelancer',           'ONLINE',  'CBS', 0, '2023-11-01 15:00:00', '2025-01-28 12:00:00');

-- raw_account
INSERT INTO raw_account VALUES
('ACC001', 'CUST001', 'SG', 'SG_BANK', 'CREDIT', 'PLATINUM_CARD', 'SGD', -2450.00,  7550.00, 10000.00, NULL,    0.0249, 'ACTIVE', NULL,      'ORCHARD', 'CC_PLAT', 'Platinum Card',       '2018-06-01', NULL, '2025-02-20', 'CBS', 0, '2018-06-01 09:00:00', '2025-02-20 00:00:01'),
('ACC002', 'CUST001', 'SG', 'SG_BANK', 'SAVINGS', 'ENHANCED_SAVINGS',  'SGD', 35420.50, 35420.50, NULL, 5000.00, 0.0350, 'ACTIVE', NULL,    'ORCHARD', 'SAV_ENH', 'Enhanced Savings',    '2018-06-01', NULL, '2025-02-19', 'CBS', 0, '2018-06-01 09:00:00', '2025-02-19 14:00:00'),
('ACC003', 'CUST002', 'SG', 'SG_BANK', 'CREDIT', 'STANDARD_CARD',      'SGD',  -980.00,  4020.00, 5000.00, NULL,  0.0249, 'ACTIVE', NULL,    'BISHAN',  'CC_STD',  'Standard Card',       '2020-03-10', NULL, '2025-02-18', 'CBS', 0, '2020-03-10 14:00:00', '2025-02-18 00:00:01'),
('ACC004', 'CUST003', 'SG', 'SG_BANK', 'CREDIT', 'INFINITE_CARD',      'SGD',-12800.00, 17200.00, 30000.00, NULL, 0.0199, 'ACTIVE', NULL,    'CLEMENTI','CC_INF',  'Infinite Card',       '2015-01-20', NULL, '2025-02-20', 'CBS', 0, '2015-01-20 11:00:00', '2025-02-20 00:00:01'),
('ACC005', 'CUST004', 'MY', 'MY_BANK', 'CREDIT', 'GOLD_CARD',           'MYR', -3200.00, 11800.00, 15000.00, NULL, 0.0499, 'ACTIVE', NULL,    'AMPANG',  'CC_GOLD', 'Gold Card',           '2019-08-15', NULL, '2025-02-19', 'CTOS',0, '2019-08-15 10:00:00', '2025-02-19 00:00:01'),
('ACC006', 'CUST005', 'MY', 'MY_BANK', 'CREDIT', 'PLATINUM_CARD',       'MYR', -8900.00, 21100.00, 30000.00, NULL, 0.0399, 'ACTIVE', NULL,    'BB_KL',   'CC_PLAT', 'Platinum Card',       '2017-04-01', NULL, '2025-02-20', 'CTOS',0, '2017-04-01 09:30:00', '2025-02-20 00:00:01'),
('ACC007', 'CUST007', 'IN', 'IN_BANK', 'CREDIT', 'STANDARD_CARD',       'INR',-18500.00,131500.00,150000.00, NULL, 0.0399, 'ACTIVE', NULL,    'BANDRA',  'CC_STD',  'Standard Card',       '2021-01-15', NULL, '2025-02-20', 'CIBIL',0,'2021-01-15 12:00:00', '2025-02-20 00:00:01'),
('ACC008', 'CUST008', 'IN', 'IN_BANK', 'CREDIT', 'PLATINUM_CARD',       'INR',-85000.00,415000.00,500000.00, NULL, 0.0350, 'ACTIVE', NULL,    'POWAI',   'CC_PLAT', 'Platinum Card',       '2016-09-10', NULL, '2025-02-20', 'CIBIL',0,'2016-09-10 10:30:00', '2025-02-20 00:00:01'),
('ACC009', 'CUST010', 'SG', 'SG_BANK', 'CREDIT', 'STANDARD_CARD',       'SGD',    0.00,  3000.00,  3000.00, NULL, 0.0249, 'FROZEN', 'FRAUD_REVIEW', 'TOAP', 'CC_STD','Standard Card',      '2023-11-01', NULL, '2025-01-15', 'CBS', 0, '2023-11-01 15:00:00', '2025-01-15 09:00:00'),
('ACC010', 'CUST009', 'IN', 'IN_BANK', 'CURRENT','PREMIUM_CURRENT',     'INR',1250000.00,1250000.00,NULL,100000.00,0.0350,'ACTIVE',NULL,       'MG_RD',   'CUR_PREM','Premium Current',     '2012-06-01', NULL, '2025-02-20', 'CIBIL',0,'2012-06-01 08:00:00', '2025-02-20 10:00:00');

-- raw_transaction (recent sample, last 30 days)
INSERT INTO raw_transaction VALUES
('TXN20250215001','ACC001','CRD001','CUST001','SG','SG_BANK','2025-02-15 12:30:00','2025-02-15 23:59:00',145.80,'SGD','PURCHASE','POS',     'MERCH001','Crystal Jade',         'FOOD',   '5812','APPROVED',NULL,          0,0.0120,NULL,0,0,0,'REF001','Crystal Jade Orchard','CBS','2025-02-15 12:30:00'),
('TXN20250215002','ACC001','CRD001','CUST001','SG','SG_BANK','2025-02-15 14:15:00','2025-02-15 23:59:00', 68.90,'SGD','PURCHASE','ONLINE',  'MERCH002','Grab',                  'FOOD',   '7299','APPROVED',NULL,          0,0.0050,NULL,0,0,1,'REF002','Grab Food delivery',  'CBS','2025-02-15 14:15:00'),
('TXN20250215003','ACC003','CRD002','CUST002','SG','SG_BANK','2025-02-15 09:00:00','2025-02-15 23:59:00', 42.50,'SGD','PURCHASE','CONTACTLESS','MERCH003','NTUC FairPrice',     'RETAIL', '5411','APPROVED',NULL,          0,0.0030,NULL,0,1,1,'REF003','NTUC FairPrice Bishan','CBS','2025-02-15 09:00:00'),
('TXN20250216001','ACC001','CRD001','CUST001','SG','SG_BANK','2025-02-16 08:45:00','2025-02-16 23:59:00',  3.50,'SGD','PURCHASE','CONTACTLESS','MERCH004','EZ-Link',            'TRAVEL', '4112','APPROVED',NULL,          0,0.0010,NULL,0,1,1,'REF004','EZ-Link auto top-up',  'CBS','2025-02-16 08:45:00'),
('TXN20250216002','ACC004','CRD003','CUST003','SG','SG_BANK','2025-02-16 20:00:00','2025-02-16 23:59:00',4850.00,'SGD','PURCHASE','ONLINE',  'MERCH005','Singapore Airlines', 'TRAVEL', '4511','APPROVED',NULL,          0,0.0150,NULL,1,0,0,'REF005','SQ flight booking',   'CBS','2025-02-16 20:00:00'),
('TXN20250217001','ACC005','CRD004','CUST004','MY','MY_BANK','2025-02-17 13:00:00','2025-02-17 23:59:00',230.00,'MYR','PURCHASE','POS',     'MERCH006','Pavilion KL',          'RETAIL', '5411','APPROVED',NULL,          0,0.0200,NULL,0,0,0,'REF006','Pavilion KL shopping',  'CTOS','2025-02-17 13:00:00'),
('TXN20250217002','ACC005','CRD004','CUST004','MY','MY_BANK','2025-02-17 21:30:00','2025-02-17 23:59:00',195.00,'MYR','PURCHASE','ONLINE',  'MERCH007','Shopee MY',            'RETAIL', '5999','APPROVED',NULL,          0,0.0080,NULL,0,0,0,'REF007','Shopee purchase',       'CTOS','2025-02-17 21:30:00'),
('TXN20250218001','ACC007','CRD005','CUST007','IN','IN_BANK','2025-02-18 11:00:00','2025-02-18 23:59:00',2800.00,'INR','PURCHASE','ONLINE',  'MERCH008','Amazon IN',            'RETAIL', '5999','APPROVED',NULL,          0,0.0060,NULL,0,0,0,'REF008','Amazon order',          'CIBIL','2025-02-18 11:00:00'),
-- Fraud/suspicious transactions
('TXN20250218002','ACC009','CRD006','CUST010','SG','SG_BANK','2025-02-18 03:12:00','2025-02-18 23:59:00',2990.00,'SGD','PURCHASE','ONLINE',  'MERCH009','CryptoMerch',          'OTHER',  '7995','DECLINED','FRAUD_SUSPECT',1,0.9200,'HIGH_RISK',1,0,0,'REF009','Flagged: high fraud score','CBS','2025-02-18 03:12:00'),
('TXN20250218003','ACC009','CRD006','CUST010','SG','SG_BANK','2025-02-18 03:15:00','2025-02-18 23:59:00',  89.00,'SGD','PURCHASE','ONLINE',  'MERCH010','Local Grocery',         'FOOD',   '5411','APPROVED',NULL,         1,0.8100,'HIGH_RISK',0,0,0,'REF010','Velocity: 2nd txn in 3 min','CBS','2025-02-18 03:15:00'),
-- More MY and IN transactions
('TXN20250219001','ACC006','CRD007','CUST005','MY','MY_BANK','2025-02-19 09:30:00','2025-02-19 23:59:00',450.00,'MYR','PURCHASE','POS',     'MERCH011','Parkson',              'RETAIL','5311','APPROVED',NULL,           0,0.0100,NULL,0,0,0,'REF011','Parkson department store','CTOS','2025-02-19 09:30:00'),
('TXN20250219002','ACC008','CRD008','CUST008','IN','IN_BANK','2025-02-19 15:00:00','2025-02-19 23:59:00',12500.00,'INR','PURCHASE','ONLINE', 'MERCH012','Taj Hotels',          'TRAVEL','7011','APPROVED',NULL,           0,0.0200,NULL,0,0,0,'REF012','Hotel booking Mumbai','CIBIL','2025-02-19 15:00:00');

-- raw_payment
INSERT INTO raw_payment VALUES
('PAY20250101001','ACC001','CUST001','SG','SG_BANK','2025-01-15 10:00:00','2025-01-20','2024-12-31',250.00, 2450.00, 2450.00,'GIRO',  'MOBILE_APP',           'PAID',    0,   0.00,'PAY-REF-001','CBS','2025-01-15 10:00:00'),
('PAY20250201001','ACC001','CUST001','SG','SG_BANK','2025-02-14 09:30:00','2025-02-20','2025-01-31',280.00, 2780.00, 2780.00,'GIRO',  'AUTO',                 'PAID',    0,   0.00,'PAY-REF-002','CBS','2025-02-14 09:30:00'),
('PAY20250101002','ACC003','CUST002','SG','SG_BANK','2025-01-18 14:00:00','2025-01-22','2024-12-31', 85.00,  950.00,  200.00,'PAYNOW','MOBILE_APP',           'PARTIAL', 0,   0.00,'PAY-REF-003','CBS','2025-01-18 14:00:00'),
('PAY20250201002','ACC003','CUST002','SG','SG_BANK',NULL,                 '2025-02-22','2025-01-31',120.00, 1080.00,    0.00,NULL,    NULL,                   'OVERDUE', 5,  25.00,'PAY-REF-004','CBS','2025-02-22 23:59:00'),
('PAY20250101003','ACC005','CUST004','MY','MY_BANK','2025-01-20 11:00:00','2025-01-25','2024-12-31',300.00, 3200.00, 3200.00,'TRANSFER','INTERNET_BANKING',   'PAID',    0,   0.00,'PAY-REF-005','CTOS','2025-01-20 11:00:00'),
('PAY20250201003','ACC007','CUST007','IN','IN_BANK','2025-02-10 08:00:00','2025-02-15','2025-01-31',1500.00,18500.00,18500.00,'UPI',   'MOBILE_APP',           'PAID',    0,   0.00,'PAY-REF-006','CIBIL','2025-02-10 08:00:00'),
('PAY20250201004','ACC009','CUST010','SG','SG_BANK',NULL,                 '2025-02-10','2025-01-31', 50.00,   180.00,    0.00,NULL,    NULL,                   'OVERDUE', 12,  50.00,'PAY-REF-007','CBS','2025-02-10 23:59:00');


-- =============================================================================
-- SEMANTIC LAYER SAMPLE DATA (loaded after ETL from raw/ddm/dp)
-- =============================================================================

-- semantic_customer_360
INSERT INTO semantic_customer_360 VALUES
('CUST001','SG','SG_BANK','Wei Tan',       'AFFLUENT', 'LOW',    'VERIFIED',40,'35-50','50K-150K',81, 'ACC001','CREDIT',  -2450.00, 7550.00, 10000.00,0.2450,2,10000.00,-2450.00,0.2450,3280.50,42,'FOOD','PAID',         2780.00, 6, 0,0,'2025-02-20','2025-02-20 06:00:00'),
('CUST002','SG','SG_BANK','Priya Nair',    'MASS',     'LOW',    'VERIFIED',33,'25-35','<50K',      60, 'ACC003','CREDIT', -980.00,  4020.00,  5000.00, 0.1960,1, 5000.00, -980.00,0.1960, 750.50,18,'RETAIL','OVERDUE', 1080.00,-10, 1,0,'2025-02-20','2025-02-20 06:00:00'),
('CUST003','SG','SG_BANK','Ahmad Ridzwan', 'PRIORITY', 'MEDIUM', 'VERIFIED',47,'35-50','150K-500K',121, 'ACC004','CREDIT',-12800.00,17200.00, 30000.00,0.4267,3,30000.00,-12800.00,0.4267,8950.00,28,'TRAVEL','PAID',        3200.00, 12, 0,0,'2025-02-20','2025-02-20 06:00:00'),
('CUST004','MY','MY_BANK','Raj Kumar',     'MASS',     'LOW',    'VERIFIED',35,'25-35','<50K',      66, 'ACC005','CREDIT', -3200.00,11800.00, 15000.00,0.2133,1,15000.00, -3200.00,0.2133,2850.00,35,'RETAIL','PAID',        3200.00, 10, 0,0,'2025-02-20','2025-02-20 06:00:00'),
('CUST005','MY','MY_BANK','Siti Rahimah',  'AFFLUENT', 'LOW',    'VERIFIED',43,'35-50','150K-500K', 96, 'ACC006','CREDIT', -8900.00,21100.00, 30000.00,0.2967,2,30000.00, -8900.00,0.2967,6200.00,22,'RETAIL','PAID',        8900.00, 15, 0,0,'2025-02-20','2025-02-20 06:00:00'),
('CUST007','IN','IN_BANK','Ravi Sharma',   'MASS',     'LOW',    'VERIFIED',37,'25-35','<50K',      49, 'ACC007','CREDIT',-18500.00,131500.00,150000.00,0.1233,1,150000.00,-18500.00,0.1233,12800.00,31,'RETAIL','PAID',       18500.00, 5, 0,0,'2025-02-20','2025-02-20 06:00:00'),
('CUST008','IN','IN_BANK','Anita Desai',   'AFFLUENT', 'MEDIUM', 'VERIFIED',45,'35-50','150K-500K',102,'ACC008','CREDIT',-85000.00,415000.00,500000.00,0.1700,2,500000.00,-85000.00,0.1700,42500.00,18,'TRAVEL','PAID',       85000.00,  8, 0,0,'2025-02-20','2025-02-20 06:00:00'),
('CUST010','SG','SG_BANK','Emily Ong',     'MASS',     'HIGH',   'PENDING', 30,'25-35','<50K',      15, 'ACC009','CREDIT',     0.00,  3000.00,  3000.00,0.0000,1, 3000.00,     0.00,0.0000,  125.00, 3,'OTHER','OVERDUE',   180.00,-12, 1,3,'2025-02-20','2025-02-20 06:00:00');

-- semantic_spend_metrics (February 2025)
INSERT INTO semantic_spend_metrics VALUES
('2025-02', 'CUST001', 'SG', 'SG_BANK', 'AFFLUENT', 3280.50, 620.50, 980.00,1420.00,  0.00, 180.00, 80.00, 0.00,  42,  8, 0.4400, 0.5600, 1420.00, 0.0250, 0.1820,'Singapore Airlines','TRAVEL','SGD','2025-02-20 06:00:00'),
('2025-02', 'CUST002', 'SG', 'SG_BANK', 'MASS',      750.50, 280.00, 420.50,  0.00, 50.00,   0.00,  0.00, 0.00,  18,  6, 0.3200, 0.6800,   0.00, 0.0340,-0.0500,'NTUC FairPrice','RETAIL','SGD','2025-02-20 06:00:00'),
('2025-02', 'CUST004', 'MY', 'MY_BANK', 'MASS',     2850.00, 320.00,1380.00,  0.00,  0.00, 350.00,800.00, 0.00, 35,  9, 0.5500, 0.4500,   0.00, 0.1200, 0.0800,'Shopee MY','RETAIL','MYR','2025-02-20 06:00:00'),
('2025-02', 'CUST007', 'IN', 'IN_BANK', 'MASS',    12800.00,2800.00,4200.00,1500.00,2200.00,1600.00,500.00,0.00,  31, 11, 0.6200, 0.3800,   0.00, 0.0950, 0.1320,'Amazon IN','RETAIL','INR','2025-02-20 06:00:00');

-- semantic_risk_metrics (recent daily)
INSERT INTO semantic_risk_metrics VALUES
('2025-02-18', 'SG', 'SG_BANK', NULL, NULL, NULL, 18450, 18120, 330, 0.01789, 42, 85000.00, 0.00228, 0.6800, 280, 8, 120, NULL, 380, 1200000.00, 0.02161, 0.00545, 0.00218, 0.00082, 'CryptoMerch', 2990.00, '2025-02-18 06:00:00'),
('2025-02-18', 'MY', 'MY_BANK', NULL, NULL, NULL, 22100, 21850, 250, 0.01131, 28, 45000.00, 0.00127, 0.5200, 195, 5,  88, NULL, 220,  680000.00, 0.01005, 0.00315, 0.00090, 0.00022, 'Unknown Online', 4500.00, '2025-02-18 06:00:00'),
('2025-02-18', 'IN', 'IN_BANK', NULL, NULL, NULL, 95200, 93800,1400, 0.01471, 185,920000.00, 0.00194, 0.4800,1250,38, 420, NULL,1850, 5800000.00, 0.01990, 0.00820, 0.00380, 0.00150, 'Suspicious_Vendor', 85000.00, '2025-02-18 06:00:00');

-- semantic_payment_status
INSERT INTO semantic_payment_status VALUES
('2025-02-20','CUST001','SG','SG_BANK','Wei Tan',       'AFFLUENT','ACC001','CREDIT','2025-01',  '2025-02-20',0,   280.00, 2780.00, 2780.00, 0.00,    'PAID',    0,'CURRENT', 0.00,1,'GIRO',   0,'2025-02-20 06:00:00'),
('2025-02-20','CUST002','SG','SG_BANK','Priya Nair',    'MASS',     'ACC003','CREDIT','2025-01', '2025-02-22',-10, 120.00, 1080.00,  200.00, 880.00,  'OVERDUE', 10,'1-30',  25.00,0,'PAYNOW', 2,'2025-02-20 06:00:00'),
('2025-02-20','CUST003','SG','SG_BANK','Ahmad Ridzwan', 'PRIORITY', 'ACC004','CREDIT','2025-01', '2025-02-28', 8,  350.00, 3200.00,    0.00,3200.00, 'DUE_SOON', 0,'CURRENT', 0.00,0,'TRANSFER',0,'2025-02-20 06:00:00'),
('2025-02-20','CUST004','MY','MY_BANK','Raj Kumar',     'MASS',     'ACC005','CREDIT','2025-01', '2025-02-25', 5,  300.00, 3200.00, 3200.00,    0.00,'PAID',     0,'CURRENT', 0.00,1,'TRANSFER',0,'2025-02-20 06:00:00'),
('2025-02-20','CUST007','IN','IN_BANK','Ravi Sharma',   'MASS',     'ACC007','CREDIT','2025-01', '2025-02-15', -5,1500.00,18500.00,18500.00,    0.00,'PAID',     0,'CURRENT', 0.00,1,'UPI',     0,'2025-02-20 06:00:00'),
('2025-02-20','CUST010','SG','SG_BANK','Emily Ong',     'MASS',     'ACC009','CREDIT','2025-01', '2025-02-10',-12,  50.00,  180.00,    0.00,  180.00,'OVERDUE',  12,'1-30',  50.00,0,NULL,      4,'2025-02-20 06:00:00');

-- semantic_portfolio_kpis (Feb 2025)
INSERT INTO semantic_portfolio_kpis VALUES
('2025-02','SG','SG_BANK',125000,98200,1850,980, 0.0185,0.0080, 135000,122000,112000, 96000, 8450000000.00,0.0350,68500.00,2150000.00,1800000.00, 0.01789,0.01200,0.00890, 2650000.00, 0.0890,0.9220,0.8550, 'SGD',0.748000,'2025-02-20 06:00:00'),
('2025-02','MY','MY_BANK', 89000,72100,1250,640, 0.0140,0.0072,  98000, 88000, 82000, 71000, 4200000000.00,0.0420,47200.00,1850000.00, 620000.00, 0.01131,0.01050,0.00640, 1250000.00, 0.0720,0.9100,0.8200, 'MYR',0.222900,'2025-02-20 06:00:00'),
('2025-02','IN','IN_BANK',380000,298000,8200,3100, 0.0216,0.0104,420000,382000,365000,310000,28500000000.00,0.0285,75900.00,12800000.00,4200000.00,0.01471,0.00890,0.00520,4500000000.00,0.0680,0.9150,0.8450,'INR',0.012050,'2025-02-20 06:00:00');
