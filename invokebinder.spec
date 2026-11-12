Name:		invokebinder
Version:	1.13
Release:	1
Summary:	MethodHandle transforms for JRuby
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/headius/invokebinder
# Tag invokebinder-1.13. Twenty Java sources plus module-info.
# JRuby 9.4.14 compiles against this artifact. Binder uses VarHandle,
# so the classes are release 9. The Gradle tool is not involved.
Source0:	invokebinder-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
com.headius:invokebinder %{version}. Binder.insert places a constant
argument on a method handle. The sources are compiled with javac.

%prep
%autosetup -n invokebinder-invokebinder-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src/main/java -name '*.java' | sort > sources.list
test "$(wc -l < sources.list)" -eq 21
grep -q module-info.java sources.list

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p classes
javac --release 9 -Xlint:-options -encoding UTF-8 -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 23
javap -v -classpath classes com.headius.invokebinder.Binder | grep -F -q 'major version: 53'
jar cf invokebinder.jar -C classes .
jar i invokebinder.jar
jar tf invokebinder.jar | grep -F -q 'com/headius/invokebinder/Binder.class'
jar tf invokebinder.jar | grep -F -q 'module-info.class'
desc=$(jar --describe-module --file invokebinder.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -q 'com.headius.invokebinder'

cat > invokebinder.pom << 'END'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.headius</groupId>
  <artifactId>invokebinder</artifactId>
  <version>1.13</version>
  <name>invokebinder</name>
  <description>MethodHandle argument transforms.</description>
  <url>https://github.com/headius/invokebinder</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact invokebinder.pom:invokebinder.jar \
	--file-name invokebinder \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/com.headius/invokebinder.sysjar"
test -s "$idx"
grep -F -q '"version": "1.13"' "$idx"
grep -F -q '"artifactId": "invokebinder"' "$idx"
test -s %{buildroot}%{_javadir}/invokebinder.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/invokebinder.jar
test -s "$JAR"
mkdir -p check
cat > check/Smoke.java << 'EOF'
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import com.headius.invokebinder.Binder;

public class Smoke {
    public static void main(String[] args) throws Throwable {
        MethodHandle sum = MethodHandles.lookup().findStatic(
            Integer.class, "sum", MethodType.methodType(int.class, int.class, int.class));
        MethodHandle add2 = Binder.from(int.class, int.class).insert(0, 2).invoke(sum);
        int got = (int) add2.invokeExact(3);
        if (got != 5) {
            throw new AssertionError(got);
        }
        System.out.println("invokebinder_ok " + got);
    }
}
EOF
javac --release 9 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
"$JAVA_HOME/bin/java" -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'invokebinder_ok 5' check/out.txt

%files -f .mfiles
%doc README.markdown
%license LICENSE
