from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field


REPORT_VERSION = 1


@dataclass(slots=True)
class ProselintWarning:
    """A single proselint warning anchored to a DOM element."""

    selector: str
    snippet: str
    check: str
    severity: str
    message: str
    replacement: str | None = None


@dataclass(slots=True)
class ProselintFileReport:
    """All proselint warnings found in a single HTML file."""

    path: str
    warnings: list[ProselintWarning] = field(default_factory=list)


@dataclass(slots=True)
class ProselintReport:
    """The full proselint report for a build."""

    version: int = REPORT_VERSION
    files: dict[str, ProselintFileReport] = field(default_factory=dict)

    def add_file(self, file_report: ProselintFileReport) -> None:
        if file_report.warnings:
            self.files[file_report.path] = file_report

    @classmethod
    def from_dict(cls, data: dict) -> "ProselintReport":
        files = {
            path: ProselintFileReport(
                path=path,
                warnings=[ProselintWarning(**w) for w in entry.get("warnings", [])],
            )
            for path, entry in data.get("files", {}).items()
        }
        return cls(version=data.get("version", REPORT_VERSION), files=files)

    def as_dict(self) -> dict:
        return asdict(self)
