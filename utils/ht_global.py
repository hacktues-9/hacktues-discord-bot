tech = [ "HTML", "C++", "TensorFlow", "Etherium", "JavaScript", "TypeScript", "Angular.js", "Samza", "IOT", "Raspberry Pi", "Rust", "Scala", "Objective C", "Node.js", "Java", "SQLite", "Kubernetes", "Machine Learing", "VR", "C#", "Kotlin", "Vue.js", "MongoDB", "RocksDB", "Perl", "C", "Go", "Flutter", "Flask", "Cassandra", "Arduino", "Docker", "Postgre SQL", "Linux", "Ruby", "Hadoop", "Swift", "Redis", "Python", "Assembler", "MySQL", "InfluxDB", "RDS", "NoSQL", "Django", "PWA", "Embedded", "MapReduce", "CSS", "Pytorch", "PHP", "React.js", "Lua", "R", "AR", "SQL", "Kafka", "Blockchain", "Unity3D" ]
classes = ['А','Б','В','Г',]
TOKEN = str(os.getenv('TOKEN'))
# split GUILD IDS by comma and put them in a list
GUILD_IDS =  [int(x) for x in os.getenv('GUILD_IDS').split(', ')]