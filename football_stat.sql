CREATE TABLE
    StatTypes (
        StatCode VARCHAR(5) PRIMARY KEY,
        Name VARCHAR(50) NOT NULL
    );

INSERT INTO
    StatTypes (StatCode, Name)
VALUES ('G', 'Гол'), ('A', 'Асистенция'), ('R', 'Червен картон'), ('Y', 'Жълт картон'), ('OG', 'Автогол'), ('IN', 'Смяна влиза'), ('OUT', 'Смяна излиза');

CREATE TABLE
    Positions (
        PositionCode VARCHAR(2) PRIMARY KEY,
        Name VARCHAR(50) NOT NULL
    );

INSERT INTO
    Positions (PositionCode, Name)
VALUES ('GK', 'Вратар'), ('RB', 'Десен защитник'), ('LB', 'Ляв защитник'), ('CB', 'Централен защитник'), ('RM', 'Десен полузащитник'), ('LM', 'Ляв полузащитник'), ('CM', 'Полузащитник'), ('CF', 'Централен нападател');

CREATE TABLE
    Players (
        Id INT PRIMARY KEY,
        Name VARCHAR(50) NOT NULL,
        Num INT NOT NULL,
        PositionCode VARCHAR(2) NOT NULL,
        FOREIGN KEY (PositionCode) REFERENCES Positions (PositionCode)
    );

INSERT INTO
    Players (Id, Name, Num, PositionCode)
VALUES (1, 'Ivaylo Trifonov', 1, 'GK'), (2, 'Valko Trifonov', 2, 'RB'), (3, 'Ognyan Yanev', 3, 'CB'), (4, 'Zahari Dragomirov', 4, 'CB'), (5, 'Bozhidar Chilikov', 5, 'LB'), (6, 'Timotei Zahariev', 6, 'CM'), (7, 'Marin Valentinov', 7, 'CM'), (8, 'Mitre Cvetkov', 99, 'CF'), (9, 'Zlatko Genov', 9, 'CF'), (10, 'Matey Goranov', 10, 'RM'), (11, 'Sergei Zhivkov', 11, 'LM');

CREATE TABLE
    Tournaments (
        Id INT PRIMARY KEY,
        Name VARCHAR(50) NOT NULL
    );

INSERT INTO
    Tournaments (Id, Name)
VALUES (1, 'Шампионска лига'), (2, 'Първа лига'), (3, 'Купа на България'), (4, 'Суперкупа на България');

CREATE TABLE
    Matches (
        Id INT PRIMARY KEY,
        MatchDate DATE NOT NULL,
        TournamentId INT NOT NULL,
        FOREIGN KEY (TournamentId) REFERENCES Tournaments (Id)
    );

INSERT INTO
    Matches (Id, MatchDate, TournamentId)
VALUES (1, '2018-04-08', 2), (2, '2018-04-13', 2), (3, '2018-04-21', 2), (4, '2018-04-28', 2), (5, '2018-05-06', 2), (6, '2018-05-11', 2), (7, '2017-09-21', 3), (8, '2017-10-26', 3);

CREATE TABLE
    MatchStats (
        Id INT PRIMARY KEY,
        MatchId INT NOT NULL,
        PlayerId INT NOT NULL,
        EventMinute INT NOT NULL,
        StatCode VARCHAR(2) NOT NULL,
        FOREIGN KEY (MatchId) REFERENCES Matches (Id),
        FOREIGN KEY (PlayerId) REFERENCES Players (Id),
        FOREIGN KEY (StatCode) REFERENCES StatTypes (StatCode)
    );

INSERT INTO
    MatchStats (
        Id,
        MatchId,
        PlayerId,
        EventMinute,
        StatCode
    )
VALUES (1, 8, 9, 14, 'G'), (2, 8, 8, 14, 'A'), (3, 8, 3, 43, 'Y'), (4, 7, 2, 28, 'Y'), (5, 7, 10, 45, 'Y'), (6, 7, 10, 65, 'R'), (7, 1, 10, 23, 'G'), (8, 1, 9, 23, 'A'), (9, 1, 9, 43, 'G'), (10, 2, 4, 33, 'OG'), (11, 2, 9, 68, 'G'), (12, 2, 1, 68, 'A'), (13, 3, 3, 35, 'G'), (14, 3, 4, 35, 'A'), (15, 3, 8, 55, 'G'), (16, 3, 11, 55, 'A'), (17, 4, 3, 9, 'G'), (18, 4, 8, 9, 'G'), (19, 4, 8, 56, 'OG'), (20, 5, 8, 67, 'G');

-- 8.

SELECT p.Name, p.Num
FROM Players p
WHERE
    p.PositionCode IN ('LB', 'CB', 'RM');

-- 9.

SELECT m.MatchDate, t.Name
FROM Matches m
    JOIN Tournaments t ON m.TournamentId = t.Id
WHERE
    m.MatchDate BETWEEN '2018-04-01' AND '2018-04-30';

-- 10.

SELECT
    m.MatchDate,
    p.Name,
    p.Num,
    ms.EventMinute,
    st.Name
FROM MatchStats ms
    JOIN Matches m ON ms.MatchId = m.Id
    JOIN Players p ON ms.PlayerId = p.Id
    JOIN StatTypes st ON ms.StatCode = st.StatCode
WHERE p.Num = 99;

-- 11.

SELECT COUNT(*) AS TotalOwnGoals
FROM MatchStats ms
    JOIN StatTypes st ON ms.StatCode = st.StatCode
WHERE st.Name = 'Own Goal';

-- 12.

SELECT
    m.MatchDate,
    COUNT(*) AS Goals
FROM MatchStats ms
    JOIN Matches m ON ms.MatchId = m.Id
WHERE
    m.MatchDate < '2018-05-01'
    AND ms.StatCode = 'G'
GROUP BY m.MatchDate;

-- 13.

SELECT
    CASE p.PositionCode
        WHEN 'GK' THEN 'Goalkeeper'
        WHEN 'LB' THEN 'Left Back'
        WHEN 'CB' THEN 'Center Back'
        WHEN 'RB' THEN 'Right Back'
        WHEN 'LM' THEN 'Left Midfielder'
        WHEN 'CM' THEN 'Center Midfielder'
        WHEN 'RM' THEN 'Right Midfielder'
        WHEN 'LW' THEN 'Left Winger'
        WHEN 'RW' THEN 'Right Winger'
        WHEN 'CF' THEN 'Center Forward'
    END AS Position,
    COUNT(*) AS Goals
FROM MatchStats ms
    JOIN Players p ON ms.PlayerId = p.Id
WHERE ms.StatCode = 'G'
GROUP BY p.PositionCode;

-- 14.

SELECT
    p.Name,
    p.Num,
    CASE p.PositionCode
        WHEN 'GK' THEN 'Goalkeeper'
        WHEN 'LB' THEN 'Left Back'
        WHEN 'CB' THEN 'Center Back'
        WHEN 'RB' THEN 'Right Back'
        WHEN 'LM' THEN 'Left Midfielder'
        WHEN 'CM' THEN 'Center Midfielder'
        WHEN 'RM' THEN 'Right Midfielder'
        WHEN 'LW' THEN 'Left Winger'
        WHEN 'RW' THEN 'Right Winger'
        WHEN 'CF' THEN 'Center Forward'
    END AS Position,
    COUNT(*) AS Cards
FROM MatchStats ms
    JOIN Players p ON ms.PlayerId = p.Id
WHERE ms.StatCode IN ('R', 'Y')
GROUP BY p.Id
ORDER BY Cards DESC;