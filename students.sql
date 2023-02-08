SELECT s.Name
FROM Subjects s
    JOIN StudentMarks sm ON sm.SubjectId = s.Id
WHERE sm.Mark IS NULL;

SELECT
    st.Name,
    st.Num,
    st.ClassNum,
    st.ClassLetter
FROM Students st
WHERE st.ClassNum IN (11, 12)
GROUP BY
    st.Name,
    st.Num,
    st.ClassNum,
    st.ClassLetter
ORDER BY
    st.ClassNum,
    st.ClassLetter,
    st.Name;

SELECT s.Name
FROM Subjects s
    JOIN StudentMarks sm ON sm.SubjectId = s.Id
GROUP BY s.Name
HAVING AVG(sm.Mark) < 2.99
ORDER BY AVG(sm.Mark);

ALTER TABLE Subjects ADD CONSTRAINT UQ_Subjects_Name UNIQUE (Name);