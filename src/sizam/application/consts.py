from enum import Enum


class UntiCourseStatus(str, Enum):
    REVIEW = "review"
    APPROVED = "approved"
    DECLINED = "declined"
    ACCEPTED = "accepted"
    TRANSFER = "transfer"
    FINISHED = "finished"
    EXPELLED = "expelled"
    UNKNOWN = "unknown"


STATUSES_MAPPING = {
    "expelled": UntiCourseStatus.EXPELLED,
    "отчислен": UntiCourseStatus.EXPELLED,
    "отичслить": UntiCourseStatus.EXPELLED,
    "зачислен": UntiCourseStatus.ACCEPTED,
    "зачислить": UntiCourseStatus.ACCEPTED,
    "accepted": UntiCourseStatus.ACCEPTED,
    "отклонена": UntiCourseStatus.DECLINED,
    "отклонить": UntiCourseStatus.DECLINED,
    "declined": UntiCourseStatus.DECLINED,
    "окончил модуль": UntiCourseStatus.FINISHED,
    "завершить модуль": UntiCourseStatus.FINISHED,
    "finished": UntiCourseStatus.FINISHED,
}