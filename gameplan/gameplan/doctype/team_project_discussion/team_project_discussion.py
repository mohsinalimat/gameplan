# Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from gameplan.utils import extract_mentions
from frappe.utils import get_fullname

class TeamProjectDiscussion(Document):
	def before_insert(self):
		self.last_post_at = frappe.utils.now()

	def on_trash(self):
		for name in frappe.db.get_all('Team Comment', {
			'reference_doctype': self.doctype,
			'reference_name': self.name
		}, pluck='name'):
			frappe.delete_doc('Team Comment', name)

		for name in frappe.db.get_all('Team Discussion Visit', {'discussion': self.name}, pluck='name'):
			frappe.delete_doc('Team Discussion Visit', name)

	def on_change(self):
		mentions = extract_mentions(self.content)
		for mention in mentions:
			values = frappe._dict(
				from_user=self.owner,
				to_user=mention.email,
				discussion=self.name,
			)
			if frappe.db.exists("Team Notification", values):
				continue
			notification = frappe.get_doc(doctype='Team Notification')
			notification.message = f'{get_fullname(self.owner)} mentioned you in a post',
			notification.update(values)
			notification.insert(ignore_permissions=True)

	@frappe.whitelist()
	def track_visit(self):
		values = {"user": frappe.session.user, "discussion": self.name}
		existing = frappe.db.get_value("Team Discussion Visit", values)
		if existing:
			visit = frappe.get_doc("Team Discussion Visit", existing)
			visit.last_visit = frappe.utils.now()
			visit.save(ignore_permissions=True)
		else:
			visit = frappe.get_doc(doctype="Team Discussion Visit")
			visit.update(values)
			visit.last_visit = frappe.utils.now()
			visit.insert(ignore_permissions=True)

	@frappe.whitelist()
	def move_to_project(self, project):
		if project == self.project:
			return

		self.project = project
		self.save()


def make_full_text_search_index():
	frappe.db.sql('ALTER TABLE `tabTeam Project Discussion` ADD FULLTEXT (title, content, owner)')
